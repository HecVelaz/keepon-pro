"""Captura de cámara con "último cuadro" (nunca procesa cuadros viejos).

Backends:
  ros2       tópico sensor_msgs/Image de camera_ros (el que se usa en la Pi del grupo:
             libcamera compilada en ~/camera_ws, ver docs/ESTADO_PI.md)
  picamera2  Raspberry Pi OS + Camera Module 3
  gstreamer  libcamerasrc vía OpenCV/GStreamer
  opencv     cv2.VideoCapture(index): webcam USB en la notebook
Un hilo lee continuamente y guarda sólo el cuadro más reciente: si la IA tarda,
se saltean cuadros en vez de acumular retraso.
"""

from __future__ import annotations

import threading
import time

import numpy as np


class StaleFrame(RuntimeError):
    """La cámara dejó de entregar cuadros nuevos."""


class Camera:
    def __init__(self, cfg: dict):
        c = cfg["camera"]
        self.w, self.h = c["size"]
        self.fps = c["fps"]
        self.backend = c["backend"]
        self.index = c["index"]
        self.ros_topic = c.get("ros_topic", "/keepon_cam/image_raw")
        self._convert = lambda f: f       # ros2 guarda el mensaje y convierte sólo lo que se procesa
        self.stamp = 0.0                  # ros2: header.stamp del último cuadro (reloj de pared)
        self._frame = None
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

    def _open_ros2(self) -> None:
        import rclpy
        from rclpy.executors import SingleThreadedExecutor
        from rclpy.node import Node
        from rclpy.qos import HistoryPolicy, QoSProfile, ReliabilityPolicy
        from sensor_msgs.msg import Image

        if not rclpy.ok():
            rclpy.init()
        self._node = Node("keepon_camera_reader")
        qos = QoSProfile(history=HistoryPolicy.KEEP_LAST, depth=1, reliability=ReliabilityPolicy.BEST_EFFORT)

        def on_image(msg):  # callback breve: sólo guarda la referencia
            with self._lock:
                self._frame, self._t = msg, time.monotonic()
                self.stamp = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
                self._n += 1

        self._node.create_subscription(Image, self.ros_topic, on_image, qos)
        self._executor = SingleThreadedExecutor()
        self._executor.add_node(self._node)
        self._convert = _image_msg_to_bgr
        self._read = None  # el hilo hace spin del executor en vez de leer

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
        if self.backend == "ros2":
            while not self._stop:
                self._executor.spin_once(timeout_sec=0.1)
            return
        while not self._stop:
            try:
                f = self._read()
            except Exception:  # noqa: BLE001
                time.sleep(0.01)
                continue
            with self._lock:
                self._frame, self._t = f, time.monotonic()
                self._n += 1

    def age(self) -> float:
        """Segundos desde que llegó el último cuadro (inf si nunca llegó)."""
        with self._lock:
            return time.monotonic() - self._t if self._frame is not None else float("inf")

    def latest(self, timeout: float = 2.0, max_age: float = 0.5) -> tuple[np.ndarray, float, int]:
        """(cuadro BGR, instante de RECEPCIÓN, número de cuadro).

        Espera el primer cuadro hasta `timeout`. Si la cámara dejó de entregar
        (el último cuadro tiene más de `max_age` s) lanza StaleFrame: nunca se
        procesa indefinidamente un cuadro congelado.
        El instante es cuando el backend entregó el cuadro, no el de exposición:
        la latencia medida con él NO incluye el retraso interno de la cámara."""
        t0 = time.monotonic()
        while True:
            with self._lock:
                if self._frame is not None:
                    if time.monotonic() - self._t > max_age:
                        raise StaleFrame(f"sin cuadros nuevos hace {time.monotonic() - self._t:.2f} s")
                    frame, t, n = self._frame, self._t, self._n
                    break
            if time.monotonic() - t0 > timeout:
                raise TimeoutError("la cámara no entrega cuadros")
            time.sleep(0.005)
        return self._convert(frame), t, n

    def close(self) -> None:
        self._stop = True
        self._th.join(timeout=1)
        if hasattr(self, "_node"):
            self._executor.shutdown()
            self._node.destroy_node()
        if hasattr(self, "cam"):
            self.cam.stop()
        if hasattr(self, "cap"):
            self.cap.release()


def _image_msg_to_bgr(msg) -> np.ndarray:
    """sensor_msgs/Image -> BGR uint8 sin cv_bridge (evita depender de su numpy)."""
    import cv2

    buf = np.frombuffer(msg.data, dtype=np.uint8).reshape(msg.height, msg.step)
    enc = msg.encoding
    ch = {"bgra8": 4, "rgba8": 4, "bgr8": 3, "rgb8": 3, "mono8": 1}.get(enc)
    if ch is None:
        raise ValueError(f"encoding no soportado: {enc}")
    img = buf[:, : msg.width * ch].reshape(msg.height, msg.width, ch) if ch > 1 else buf[:, : msg.width]
    return {"bgra8": lambda: cv2.cvtColor(img, cv2.COLOR_BGRA2BGR),
            "rgba8": lambda: cv2.cvtColor(img, cv2.COLOR_RGBA2BGR),
            "rgb8": lambda: cv2.cvtColor(img, cv2.COLOR_RGB2BGR),
            "mono8": lambda: cv2.cvtColor(img, cv2.COLOR_GRAY2BGR),
            "bgr8": lambda: img.copy()}[enc]()
