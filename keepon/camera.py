"""Captura de cámara con "último cuadro" (nunca procesa cuadros viejos).

Backends:
  picamera2  Raspberry Pi 5 + Camera Module 3 (recomendado en la Pi)
  gstreamer  libcamerasrc vía OpenCV/GStreamer (alternativa si no hay picamera2)
  opencv     cv2.VideoCapture(index): webcam USB en la notebook
Un hilo lee continuamente y guarda sólo el cuadro más reciente: si la IA tarda,
se saltean cuadros en vez de acumular retraso.
"""

from __future__ import annotations

import threading
import time

import numpy as np


class Camera:
    def __init__(self, cfg: dict):
        c = cfg["camera"]
        self.w, self.h = c["size"]
        self.fps = c["fps"]
        self.backend = c["backend"]
        self.index = c["index"]
        self._frame: np.ndarray | None = None
        self._t = 0.0
        self._n = 0
        self._lock = threading.Lock()
        self._stop = False
        self._open()
        self._th = threading.Thread(target=self._loop, daemon=True)
        self._th.start()

    # ------------------------------------------------------------ apertura
    def _open(self) -> None:
        order = [self.backend] if self.backend != "auto" else ["picamera2", "gstreamer", "opencv"]
        errors = []
        for b in order:
            try:
                getattr(self, f"_open_{b}")()
                self.backend = b
                return
            except Exception as e:  # noqa: BLE001 - se prueba el siguiente backend
                errors.append(f"{b}: {e}")
        raise RuntimeError("No se pudo abrir la cámara:\n  " + "\n  ".join(errors))

    def _open_picamera2(self) -> None:
        from picamera2 import Picamera2

        self.cam = Picamera2()
        conf = self.cam.create_video_configuration(
            main={"size": (self.w, self.h), "format": "RGB888"},  # RGB888 de libcamera = BGR en memoria
            controls={"FrameRate": self.fps})
        self.cam.configure(conf)
        self.cam.start()
        self._read = lambda: self.cam.capture_array("main")

    def _open_gstreamer(self) -> None:
        import cv2

        pipe = (f"libcamerasrc ! video/x-raw,width={self.w},height={self.h},framerate={self.fps}/1 ! "
                "videoconvert ! video/x-raw,format=BGR ! appsink drop=true max-buffers=1 sync=false")
        cap = cv2.VideoCapture(pipe, cv2.CAP_GSTREAMER)
        if not cap.isOpened():
            raise RuntimeError("libcamerasrc no disponible")
        self._cv(cap)

    def _open_opencv(self) -> None:
        import cv2

        cap = cv2.VideoCapture(self.index, cv2.CAP_V4L2)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.w)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.h)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        if not cap.isOpened():
            raise RuntimeError(f"/dev/video{self.index} no abre")
        self._cv(cap)

    def _cv(self, cap) -> None:
        self.cap = cap

        def read():
            ok, f = cap.read()
            if not ok:
                raise RuntimeError("cuadro perdido")
            return f
        self._read = read

    # ------------------------------------------------------------ lectura
    def _loop(self) -> None:
        while not self._stop:
            try:
                f = self._read()
            except Exception:  # noqa: BLE001
                time.sleep(0.01)
                continue
            with self._lock:
                self._frame, self._t = f, time.monotonic()
                self._n += 1

    def latest(self, timeout: float = 2.0) -> tuple[np.ndarray, float, int]:
        """(cuadro BGR, instante de captura, número de cuadro). Espera el primero."""
        t0 = time.monotonic()
        while True:
            with self._lock:
                if self._frame is not None:
                    return self._frame, self._t, self._n
            if time.monotonic() - t0 > timeout:
                raise TimeoutError("la cámara no entrega cuadros")
            time.sleep(0.005)

    def close(self) -> None:
        self._stop = True
        self._th.join(timeout=1)
        if hasattr(self, "cam"):
            self.cam.stop()
        if hasattr(self, "cap"):
            self.cap.release()
