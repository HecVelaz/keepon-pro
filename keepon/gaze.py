"""Control de mirada (T3) y selección del foco de atención (T4).

Error de la cara en la imagen, en grados:

    e_yaw   =  atan((u - cx) / fx)
    e_pitch = -atan((v - cy) / fy) - abajo (v crece hacia abajo)

Dos modos (gaze.modo de config.yaml):

- "objetivo" (por defecto desde el 05/11): dirección de la persona en ángulos del cuello
      d = cuello_en_la_captura + e
  `cuello_en_la_captura` es dónde miraba la cámara cuando se sacó la foto: así el atraso de la percepción
  (~100 ms) no hace que se pase. Si d se aparta del objetivo actual más que gaze.umbral_deg, el objetivo
  pasa a ser d, una sola vez: el firmware hace el movimiento con su perfil (vmax/amax), decidido, y después
  el cuello queda QUIETO con la misma referencia. Los servos vibran cuando se mueven lento (RDS3218 y
  MG996R, 05/11): mejor pocos movimientos firmes que una corrección chica en cada ciclo.
- "velocidad" (el de antes): ref += sat(kp * e) * dt en cada ciclo, con zona muerta suave.

`abajo` (gaze.mirar_abajo_deg) deja la cara un poco por encima del centro: la cámara apunta más abajo
para que entre el torso y se vea la camiseta (el campo vertical de la cámara es angosto, ±14°).

Convención de signos: yaw positivo gira hacia la DERECHA de la imagen, pitch
positivo mira hacia ARRIBA. Verificarlo físicamente al montar la cabeza.
"""

from __future__ import annotations

import math

from .world import Person, World


def _sat(x: float, lim: float) -> float:
    return max(-lim, min(lim, x))


class GazeController:
    """Zona muerta SUAVE: la velocidad es proporcional a (|e| - dz), así es continua.
    Una zona muerta dura (0 adentro, kp*e afuera) hace que el seguimiento de una
    persona que camina avance a saltos: el error de régimen v/kp cae en el borde."""

    def __init__(self, cfg: dict):
        g = cfg["gaze"]
        self.modo = g.get("modo", "velocidad")
        self.umbral = self._por_eje(g.get("umbral_deg", 2.5))   # [yaw, pitch] [°]
        self.quieto = g.get("quieto_deg", 1.0)
        self.limites = [cfg["neck"]["limits"]["yaw"], cfg["neck"]["limits"]["pitch"]]
        # kp y ema pueden ser un número (igual para los dos ejes) o una lista [yaw, pitch]:
        # el yaw (RDS3218) vibra si se mueve lento, y el pitch (MG996R) golpea si se mueve brusco.
        self.kp = self._por_eje(g["kp"])
        self.vmax = g["vmax"]
        self.dz = g["deadzone"]
        self.alpha = self._por_eje(g["ema"])
        self.abajo = g.get("mirar_abajo_deg", 0.0)
        self.reset()

    def reset(self) -> None:
        self.ex = self.ey = 0.0
        self.objetivo: list[float] | None = None   # [yaw, pitch] que se le está mandando al cuello (modo objetivo)

    @staticmethod
    def _por_eje(x) -> list[float]:
        """Devuelve [yaw, pitch]: un número vale para los dos ejes."""
        return [float(x), float(x)] if isinstance(x, (int, float)) else [float(x[0]), float(x[1])]

    @staticmethod
    def _soft_dz(e: float, dz: float) -> float:
        return math.copysign(max(0.0, abs(e) - dz), e)

    def update(self, ref: list[float], p: Person, w: World, dt: float,
               cuello: tuple[float, float, float] | None = None) -> list[float]:
        """Nueva referencia [yaw, pitch, roll]. `cuello`: posición del cuello cuando se capturó el cuadro
        (Context.cuello_captura). Sin ella, el modo objetivo no se puede usar y se sigue en velocidad."""
        # Se centra al rostro en el CENTRO ÓPTICO (cx, cy), no en el centro de la imagen:
        # con la calibración actual están 108 px corridos en u (≈ 6,5° de error en yaw).
        ex = math.degrees(math.atan((p.u - w.cx) / w.fx))
        ey = -math.degrees(math.atan((p.v - w.cy) / w.fy)) - self.abajo
        if self.modo == "objetivo" and cuello is not None:
            return self._por_objetivo(ref, ex, ey, cuello)
        self.objetivo = None
        self.ex += self.alpha[0] * (ex - self.ex)
        self.ey += self.alpha[1] * (ey - self.ey)
        dzx = math.degrees(math.atan(self.dz * w.img_w / w.fx))
        dzy = math.degrees(math.atan(self.dz * w.img_h / w.fy))
        vy = _sat(self.kp[0] * self._soft_dz(self.ex, dzx), self.vmax[0])
        vp = _sat(self.kp[1] * self._soft_dz(self.ey, dzy), self.vmax[1])
        return [ref[0] + vy * dt, ref[1] + vp * dt, ref[2]]

    def _por_objetivo(self, ref, ex: float, ey: float, cuello) -> list[float]:
        d = (cuello[0] + ex, cuello[1] + ey)          # dónde está la persona, en ángulos del cuello
        # ex/ey quedan como "error respecto de la referencia": así ref + ex sigue siendo la dirección de la
        # persona (la usa la curiosidad de Tracking para saber si está quieta).
        self.ex, self.ey = d[0] - ref[0], d[1] - ref[1]
        if self.objetivo is None:                       # recién empieza: arranca desde la referencia actual
            self.objetivo = [ref[0], ref[1]]
        for i in range(2):
            # Solo se corrige con fotos sacadas con el cuello QUIETO en el objetivo. Mientras se mueve, el
            # servo real va un poco atrás de la trayectoria del espejo y el ángulo de la foto no es exacto:
            # corregir con esas fotos lo haría ir y volver.
            llego = abs(cuello[i] - self.objetivo[i]) <= self.quieto
            if llego and abs(d[i] - self.objetivo[i]) > self.umbral[i]:
                lo, hi = self.limites[i]
                self.objetivo[i] = min(max(d[i], lo), hi)   # recortado: si no, nunca "llega" al objetivo
        return [self.objetivo[0], self.objetivo[1], ref[2]]


class Focus:
    """Elige a quién mirar. Prefiere a quien ME_MIRA; si nadie, al más cercano/centrado.
    Cambia de objetivo sólo si el candidato es mejor durante switch_after_s (histéresis)."""

    def __init__(self, cfg: dict):
        f = cfg["focus"]
        self.switch_after = f["switch_after_s"]
        self.w = (f["w_looking"], f["w_size"], f["w_center"])
        self.lost_hold = cfg["gaze"]["lost_hold_s"]
        self.target: int | None = None
        self._cand: int | None = None
        self._cand_since = 0.0

    def score(self, p: Person, w: World) -> tuple[bool, float]:
        """(mira, puntaje). ME_MIRA tiene prioridad estricta (T4); tamaño y centrado
        sólo ordenan dentro de cada grupo."""
        _, ws, wc = self.w
        centered = 1.0 - min(1.0, abs(p.u - w.cx) / (w.img_w / 2))  # "centrada" = cerca del eje óptico
        return p.looking, ws * min(1.0, p.size / w.img_h) + wc * centered

    def _better(self, a: Person, b: Person, w: World) -> bool:
        """¿a es claramente mejor que b? La histéresis temporal se aplica afuera."""
        (la, sa), (lb, sb) = self.score(a, w), self.score(b, w)
        return la > lb or (la == lb and sa > sb + 0.1)

    def update(self, w: World) -> int | None:
        visible = [p for p in w.persons.values() if p.last_seen >= w.t - 1e-9]
        cur = w.persons.get(self.target) if self.target is not None else None
        if cur is not None and w.t - cur.last_seen > self.lost_hold:
            cur = None  # perdido más de lost_hold -> se libera el objetivo
        if cur is None:
            self._cand = None
            self.target = max(visible, key=lambda p: self.score(p, w)).id if visible else None
            return self.target
        if not w.visible(cur.id):
            return self.target  # pérdida momentánea (< lost_hold): mantener
        best = max(visible, key=lambda p: self.score(p, w))
        if best.id != self.target and self._better(best, cur, w):
            if self._cand != best.id:
                self._cand, self._cand_since = best.id, w.t
            elif w.t - self._cand_since >= self.switch_after:
                self.target, self._cand = best.id, None
        else:
            self._cand = None
        return self.target
