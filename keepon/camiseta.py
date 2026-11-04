"""Detector de camisetas (T2: CAMISETA_OLIMPIA / CAMISETA_CERRO) con reglas de color y patrón sobre el torso.

Método decidido el 15/10 (docs/DECISIONES.md): reglas, no una red entrenada. Desarrollo propio.

1. Torso: un rectángulo debajo de los hombros que da Pose (MediaPipe). Se escala con el ancho de hombros, así
   no depende de la distancia. Se recorta un poco a los costados (brazos) y arriba (cuello).
2. Cada píxel se pasa a HSV y se marca como ROJO o AZUL (azul marino; la NoIR lo ve violeta).
3. Reglas, pensadas para minimizar falsos positivos (la guía: "una remera lisa roja o azul no es de Cerro, ni
   una remera blanca lisa es de Olimpia"):
   - CERRO: hay columnas del torso mayormente rojas Y columnas mayormente azules, cerca una de otra (un borde
     vertical). Sirve para la titular a rayas y para la 2026 mitad y mitad. Una lisa roja no tiene azul y una
     lisa azul no tiene rojo.
   - OLIMPIA: de arriba abajo, claro → franja oscura → claro (la franja horizontal negra), con las partes claras
     poco saturadas (blancas). Se compara el brillo de cada franja con el de la más oscura, no con un valor fijo:
     así aguanta cambios de luz. Una blanca lisa no tiene franja oscura; una oscura lisa no tiene partes claras.
   - Si no se puede mirar el torso (sin hombros, muy chico o casi todo fuera del cuadro): None (desconocida).
Limitación conocida: una camiseta roja y azul a rayas de otro club (p. ej. Barcelona) da CERRO.

Los umbrales están en config.yaml (sección `camiseta`) y salen de grabar las camisetas reales con la NoIR
(pruebas_camisetas/README.md).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

OLIMPIA, CERRO, OTRA = "OLIMPIA", "CERRO", "OTRA"


@dataclass
class Resultado:
    clase: str | None                       # OLIMPIA | CERRO | OTRA | None (no se pudo mirar el torso)
    roi: tuple[int, int, int, int] | None   # x1, y1, x2, y2 del torso evaluado [px]
    detalle: dict = field(default_factory=dict)  # números de las reglas (para el log y para ajustar)


def roi_torso(pose: dict, shape: tuple, c: dict) -> tuple[tuple[int, int, int, int] | None, str]:
    """Rectángulo del torso a partir de los hombros. Devuelve (roi, motivo); roi = None si no sirve."""
    hi, hd = pose.get("hombro_i"), pose.get("hombro_d")
    if hi is None or hd is None or min(hi[2], hd[2]) < c["vis_min"]:
        return None, "sin hombros"
    h, w = shape[:2]
    xa, xb = sorted((hi[0], hd[0]))
    ancho = xb - xa
    if ancho < c["ancho_min_px"]:
        return None, "torso chico"
    y_hombros = (hi[1] + hd[1]) / 2
    x1, x2 = xa + c["margen_lados"] * ancho, xb - c["margen_lados"] * ancho
    y1, y2 = y_hombros + c["desde_hombros"] * ancho, y_hombros + c["hasta_hombros"] * ancho
    alto = y2 - y1
    x1c, x2c, y1c, y2c = max(0, int(x1)), min(w, int(x2)), max(0, int(y1)), min(h, int(y2))
    if x2c <= x1c or y2c <= y1c or (y2c - y1c) < c["visible_min"] * alto or (x2c - x1c) < c["visible_min"] * (x2 - x1):
        return None, "torso fuera del cuadro"
    return (x1c, y1c, x2c, y2c), ""


def mascaras(hsv: np.ndarray, c: dict) -> tuple[np.ndarray, np.ndarray]:
    """Píxeles ROJOS y AZULES (HSV de OpenCV: H 0..179, S y V 0..255)."""
    hh, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    r = c["rojo"]
    rojo = ((hh <= r["h_max"]) | (hh >= r["h_min"])) & (s >= r["s_min"]) & (v >= r["v_min"])
    a = c["azul"]
    azul = (hh >= a["h_min"]) & (hh <= a["h_max"]) & (s >= a["s_min"]) & (v >= a["v_min"]) & (v <= a["v_max"])
    return rojo, azul


def regla_cerro(rojo: np.ndarray, azul: np.ndarray, c: dict) -> tuple[bool, dict]:
    """Columnas mayormente rojas y columnas mayormente azules, separadas por a lo sumo `cerro_hueco` columnas."""
    n = c["columnas"]
    fr = np.array([m.mean() for m in np.array_split(rojo, n, axis=1)])
    fa = np.array([m.mean() for m in np.array_split(azul, n, axis=1)])
    tipo = np.where(fr >= c["col_dominante"], 1, np.where(fa >= c["col_dominante"], 2, 0))  # 1 rojo, 2 azul
    cols_r, cols_a = np.flatnonzero(tipo == 1), np.flatnonzero(tipo == 2)
    borde = bool(len(cols_r) and len(cols_a)
                 and np.abs(cols_r[:, None] - cols_a[None, :]).min() <= c["cerro_hueco"] + 1)
    ok = (len(cols_r) >= c["cerro_cols_min"] and len(cols_a) >= c["cerro_cols_min"] and borde
          and rojo.mean() >= c["cerro_frac_min"] and azul.mean() >= c["cerro_frac_min"])
    return ok, {"rojo": round(float(rojo.mean()), 2), "azul": round(float(azul.mean()), 2),
                "cols": "".join(".RA"[t] for t in tipo)}


def regla_olimpia(hsv: np.ndarray, c: dict) -> tuple[bool, dict]:
    """De arriba abajo: claro → franja oscura → claro. Brillo de cada franja horizontal = mediana de V."""
    n = c["filas"]
    bandas = np.array_split(hsv, n, axis=0)
    v = np.array([np.median(b[..., 2]) for b in bandas])
    s = np.array([np.median(b[..., 1]) for b in bandas])
    k = int(np.argmin(v))
    oscura = max(float(v[k]), 1.0)

    def clara(i: int) -> bool:  # bastante más brillante que la franja y poco saturada (blanca, no de color)
        return v[i] >= c["olimpia_contraste"] * oscura and s[i] <= c["blanco_s_max"]

    arriba = any(clara(i) for i in range(k))
    abajo = any(clara(i) for i in range(k + 1, n))
    ok = arriba and abajo and oscura <= c["franja_v_max"]
    return ok, {"v": [int(x) for x in v], "franja": k}


def clasificar_hsv(hsv: np.ndarray, c: dict) -> tuple[str, dict]:
    """Clase de un torso ya recortado y pasado a HSV."""
    rojo, azul = mascaras(hsv, c)
    es_cerro, d_c = regla_cerro(rojo, azul, c)
    es_olimpia, d_o = regla_olimpia(hsv, c)
    detalle = {**d_c, **d_o}
    if es_cerro and not es_olimpia:
        return CERRO, detalle
    if es_olimpia and not es_cerro:
        return OLIMPIA, detalle
    return OTRA, detalle  # ninguna, o las dos a la vez (ambiguo: mejor no reaccionar)


def detectar(frame_bgr: np.ndarray, pose: dict, cfg: dict) -> Resultado:
    """Clase de la camiseta de una persona. pose: {nombre: (x, y, visibilidad)} como lo arma perception.py."""
    import cv2

    c = cfg["camiseta"]
    roi, motivo = roi_torso(pose, frame_bgr.shape, c)
    if roi is None:
        return Resultado(None, None, {"motivo": motivo})
    x1, y1, x2, y2 = roi
    hsv = cv2.cvtColor(frame_bgr[y1:y2, x1:x2], cv2.COLOR_BGR2HSV)
    clase, detalle = clasificar_hsv(hsv, c)
    return Resultado(clase, roi, detalle)


class FiltroCamiseta:
    """Filtro temporal por persona (T6 d): `confirmar` cuadros seguidos con la misma clase para mostrarla y
    `soltar` cuadros seguidos sin ella para dejar de mostrarla. Un cuadro sin torso visible (None) no cuenta ni
    a favor ni en contra: la persona no se quitó la camiseta porque Pose no la vio un instante."""

    def __init__(self, confirmar: int, soltar: int):
        self.confirmar, self.soltar = confirmar, soltar
        self.activa: str | None = None       # OLIMPIA | CERRO | None
        self._cand: str | None = None
        self._n = 0                           # cuadros seguidos de _cand (o sin la activa)

    def actualizar(self, clase: str | None) -> str | None:
        if clase is None:
            return self.activa
        nueva = clase if clase in (OLIMPIA, CERRO) else None
        if nueva == self.activa:
            self._cand, self._n = None, 0
            return self.activa
        if nueva != self._cand:
            self._cand, self._n = nueva, 0
        self._n += 1
        # Si cambia directo de una camiseta a otra, alcanza con `confirmar` cuadros seguidos de la nueva.
        if self._n >= (self.confirmar if nueva is not None else self.soltar):
            self.activa, self._cand, self._n = nueva, None, 0
        return self.activa
