"""Tracker de personas por superposición de cajas (IoU). Desarrollo propio.

El tracker de ultralytics (ByteTrack) costaba ~68 ms por cuadro en la Pi 5 con una
sola persona (YOLO pasaba de 20 a 89 ms). Para 1-3 personas alcanza con esto:

  1. Predice cada track con su velocidad (caja desplazada).
  2. Asocia detecciones a tracks de forma codiciosa por IoU decreciente (>= iou_min);
     si no hay superposición, por cercanía de centros (<= dist_max · ancho de la caja).
  3. Detección sin asociar -> track nuevo con ID nuevo.
     Track sin detección -> se conserva `max_lost` cuadros (oclusiones breves) sin
     cambiar de ID, así los cooldowns por persona no se reinician.
"""

from __future__ import annotations

from dataclasses import dataclass


def iou(a, b) -> float:
    ix = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / union if union > 0 else 0.0


@dataclass
class Track:
    id: int
    box: tuple
    vx: float = 0.0
    vy: float = 0.0
    lost: int = 0
    hits: int = 1

    def predicted(self) -> tuple:
        x1, y1, x2, y2 = self.box
        return (x1 + self.vx, y1 + self.vy, x2 + self.vx, y2 + self.vy)


class IoUTracker:
    def __init__(self, iou_min: float = 0.25, dist_max: float = 0.6, max_lost: int = 15, alpha: float = 0.5):
        self.iou_min, self.dist_max, self.max_lost, self.alpha = iou_min, dist_max, max_lost, alpha
        self.tracks: list[Track] = []
        self._next = 1

    def update(self, boxes: list[tuple]) -> list[int]:
        """Recibe las cajas del cuadro y devuelve el ID de cada una (mismo orden)."""
        pairs = []
        for ti, t in enumerate(self.tracks):
            pb = t.predicted()
            pw = pb[2] - pb[0]
            pc = ((pb[0] + pb[2]) / 2, (pb[1] + pb[3]) / 2)
            for di, b in enumerate(boxes):
                ov = iou(pb, b)
                if ov >= self.iou_min:
                    pairs.append((1.0 + ov, ti, di))  # la superposición manda sobre la distancia
                else:
                    bc = ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)
                    d = ((pc[0] - bc[0]) ** 2 + (pc[1] - bc[1]) ** 2) ** 0.5
                    if d <= self.dist_max * max(pw, 1.0):
                        pairs.append((1.0 - d / (self.dist_max * max(pw, 1.0)), ti, di))
        pairs.sort(reverse=True)
        ids = [0] * len(boxes)
        used_t, used_d = set(), set()
        for _, ti, di in pairs:
            if ti in used_t or di in used_d:
                continue
            used_t.add(ti)
            used_d.add(di)
            t, b = self.tracks[ti], boxes[di]
            cx_old, cy_old = (t.box[0] + t.box[2]) / 2, (t.box[1] + t.box[3]) / 2
            cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
            t.vx += self.alpha * ((cx - cx_old) - t.vx)
            t.vy += self.alpha * ((cy - cy_old) - t.vy)
            t.box, t.lost = tuple(b), 0
            t.hits += 1
            ids[di] = t.id
        for ti, t in enumerate(self.tracks):
            if ti not in used_t:
                t.lost += 1
                t.box = t.predicted()
        self.tracks = [t for t in self.tracks if t.lost <= self.max_lost]
        for di, b in enumerate(boxes):
            if di not in used_d:
                t = Track(self._next, tuple(b))
                self._next += 1
                self.tracks.append(t)
                ids[di] = t.id
        return ids
