"""Camera frame source: Pi Camera Module on a Raspberry Pi, USB webcam elsewhere."""
from __future__ import annotations

from PIL import Image


class Camera:
    def __init__(self, resolution: tuple[int, int] = (640, 480)):
        self._resolution = resolution
        self._backend = None
        self._picam2 = None
        self._cv_capture = None
        self._open()

    def _open(self) -> None:
        try:
            from picamera2 import Picamera2

            self._picam2 = Picamera2()
            config = self._picam2.create_still_configuration(
                main={"size": self._resolution, "format": "RGB888"}
            )
            self._picam2.configure(config)
            self._picam2.start()
            self._backend = "picamera2"
            return
        except ImportError:
            pass

        import cv2

        self._cv_capture = cv2.VideoCapture(0)
        if not self._cv_capture.isOpened():
            raise RuntimeError("No camera available (tried Pi Camera and USB webcam)")
        self._backend = "opencv"

    def capture(self) -> Image.Image:
        if self._backend == "picamera2":
            frame = self._picam2.capture_array()
            return Image.fromarray(frame)

        import cv2

        ok, frame = self._cv_capture.read()
        if not ok:
            raise RuntimeError("Failed to read frame from camera")
        return Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

    def close(self) -> None:
        if self._backend == "picamera2" and self._picam2 is not None:
            self._picam2.stop()
        elif self._backend == "opencv" and self._cv_capture is not None:
            self._cv_capture.release()

    def __enter__(self) -> "Camera":
        return self

    def __exit__(self, *exc_info) -> None:
        self.close()
