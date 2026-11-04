"""Eventos de T2 con filtro temporal: de la percepción cruda (cuadro a cuadro) al World.

- ME_MIRA sostenido: la cara mira a la cámara (FaceObs.looking, umbral looking_deg) durante
  `mira_sostenida_s` seguidos para activarse, y deja de mirar durante `mira_suelta_s` seguidos para
  soltarse (histéresis: un cuadro suelto no lo prende ni lo apaga).
- SALUDO: una muñeca por encima de su hombro que oscila de costado. Se cuentan los vaivenes (cambios
  de sentido con amplitud mínima, medida en anchos de hombros para no depender de la distancia).
  `saludo_ciclos` ciclos (2 vaivenes cada uno) dentro de `saludo_ventana_s` → un evento: se incrementa
  Person.wave_count. Después la mano tiene que bajar para poder contar otro saludo (un gesto = una respuesta).

Las poses (MediaPipe) no traen ID: cada una se asocia a la persona cuya caja contiene sus hombros.
Todo es por tiempo (no por cantidad de cuadros) porque la percepción no va a ritmo fijo.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .world import World


@dataclass
class _Mira:
    activo: bool = False
    desde: float | None = None  # desde cuándo el valor crudo es distinto del filtrado


@dataclass
class _Mano:
    """Vaivenes de una muñeca levantada, en coordenada x relativa al hombro [anchos de hombros]."""
    extremo: float | None = None
    sentido: int = 0                       # +1 / −1 hacia donde va; 0 = todavía no se movió lo suficiente
    vaivenes: list[float] = field(default_factory=list)  # instantes de cada cambio de sentido
    abajo_desde: float | None = None
    armada: bool = True                    # False tras un saludo, hasta que la mano baje

    def reiniciar(self) -> None:
        self.extremo, self.sentido, self.vaivenes = None, 0, []


@dataclass
class _Persona:
    mira: _Mira = field(default_factory=_Mira)
    manos: dict[str, _Mano] = field(default_factory=lambda: {"i": _Mano(), "d": _Mano()})
    saludos: int = 0
    visto: float = 0.0


class Eventos:
    """Guarda el estado por persona y completa World.persons con looking y wave_count filtrados."""

    OLVIDAR_S = 10.0  # una persona que no se ve hace más que esto se olvida

    def __init__(self, cfg: dict, log=None):
        e = cfg["eventos"]
        self.mira_on, self.mira_off = e["mira_sostenida_s"], e["mira_suelta_s"]
        self.vaivenes_min = 2 * e["saludo_ciclos"] - 1  # el primer recorrido marca el sentido, no es un vaivén
        self.ventana = e["saludo_ventana_s"]
        self.amp = e["saludo_amp_hombros"]
        self.margen = e["saludo_margen_hombros"]
        self.mano_abajo_s = e["saludo_mano_abajo_s"]
        self.vis_min = e["pose_vis_min"]
        self.log = log or (lambda t, m: None)
        self.personas: dict[int, _Persona] = {}
        self._ultima_pose = None  # frame de la última pose procesada (cada pose cuenta una sola vez)

    # -------------------------------------------------------------- entrada
    def aplicar(self, w: World, pose=None, cajas: dict[int, tuple] | None = None, crudo_mira=None) -> World:
        """Actualiza los filtros con el mundo crudo del instante w.t y lo devuelve con los eventos filtrados.

        pose: último DetResult de pose (o None). cajas: {id: (x1, y1, x2, y2)} de las personas, para asociar
        las poses. crudo_mira: {id: bool} con ME_MIRA cuadro a cuadro (por defecto, Person.looking)."""
        t = w.t
        for pid, p in w.persons.items():
            st = self.personas.setdefault(pid, _Persona())
            st.visto = t
            self._filtrar_mira(pid, st, (crudo_mira or {}).get(pid, p.looking), t)
        if pose is not None and cajas and pose.frame != self._ultima_pose:
            self._ultima_pose = pose.frame
            for kp in pose.poses:
                pid = self._asociar(kp, cajas)
                if pid is not None and pid in w.persons:
                    self._saludo(pid, self.personas[pid], kp, t)
        for pid, p in w.persons.items():
            st = self.personas[pid]
            p.looking, p.wave_count = st.mira.activo, st.saludos
        for pid in [k for k, s in self.personas.items() if t - s.visto > self.OLVIDAR_S]:
            del self.personas[pid]
        return w

    # -------------------------------------------------------------- ME_MIRA
    def _filtrar_mira(self, pid: int, st: _Persona, crudo: bool, t: float) -> None:
        m = st.mira
        if crudo == m.activo:
            m.desde = None
            return
        if m.desde is None:
            m.desde = t
        if t - m.desde >= (self.mira_on if crudo else self.mira_off):
            m.activo, m.desde = crudo, None
            self.log(t, f"EVENTO ME_MIRA persona={pid} {'SI' if crudo else 'NO'}")

    # -------------------------------------------------------------- SALUDO
    def _visible(self, kp: dict, nombre: str) -> tuple[float, float] | None:
        x, y, vis = kp.get(nombre, (0.0, 0.0, 0.0))
        return (x, y) if vis >= self.vis_min else None

    def _asociar(self, kp: dict, cajas: dict[int, tuple]) -> int | None:
        """La persona cuya caja contiene el punto medio de los hombros (o la nariz); la más cercana al centro."""
        hi, hd = self._visible(kp, "hombro_i"), self._visible(kp, "hombro_d")
        punto = ((hi[0] + hd[0]) / 2, (hi[1] + hd[1]) / 2) if hi and hd else self._visible(kp, "nariz")
        if punto is None:
            return None
        x, y = punto
        mejor, dist = None, float("inf")
        for pid, (x1, y1, x2, y2) in cajas.items():
            if x1 <= x <= x2 and y1 <= y <= y2:
                d = (x - (x1 + x2) / 2) ** 2 + (y - (y1 + y2) / 2) ** 2
                if d < dist:
                    mejor, dist = pid, d
        return mejor

    def _saludo(self, pid: int, st: _Persona, kp: dict, t: float) -> None:
        hi, hd = self._visible(kp, "hombro_i"), self._visible(kp, "hombro_d")
        if not (hi and hd):
            return
        ancho = abs(hi[0] - hd[0])
        if ancho < 1.0:
            return
        for lado, hombro in (("i", hi), ("d", hd)):
            mano, muneca = st.manos[lado], self._visible(kp, f"muneca_{lado}")
            arriba = muneca is not None and muneca[1] < hombro[1] - self.margen * ancho  # y crece hacia abajo
            if not arriba:
                if mano.abajo_desde is None:
                    mano.abajo_desde = t
                if t - mano.abajo_desde >= self.mano_abajo_s:  # bajó de verdad: se puede contar otro saludo
                    mano.reiniciar()
                    mano.armada = True
                continue
            mano.abajo_desde = None
            if not mano.armada:
                continue
            x = (muneca[0] - hombro[0]) / ancho
            if self._vaiven(mano, x, t):
                st.saludos += 1
                mano.reiniciar()
                mano.armada = False
                self.log(t, f"EVENTO SALUDO persona={pid} mano={lado} (n.º {st.saludos})")

    def _vaiven(self, m: _Mano, x: float, t: float) -> bool:
        """Registra la muestra; True si ya hay suficientes vaivenes dentro de la ventana."""
        if m.extremo is None:
            m.extremo = x
        elif m.sentido == 0:
            if abs(x - m.extremo) >= self.amp:
                m.sentido, m.extremo = (1 if x > m.extremo else -1), x
        elif (x - m.extremo) * m.sentido > 0:
            m.extremo = x  # sigue en el mismo sentido: el extremo se corre
        elif abs(x - m.extremo) >= self.amp:  # volvió lo suficiente: cambio de sentido = vaivén
            m.sentido, m.extremo = -m.sentido, x
            m.vaivenes.append(t)
        m.vaivenes = [v for v in m.vaivenes if t - v <= self.ventana]
        return len(m.vaivenes) >= self.vaivenes_min
