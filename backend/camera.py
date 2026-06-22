"""
Camera abstraction for L.I.T.H.O.S.

On a Raspberry Pi with picamera2 installed, uses the CSI camera.
On any other machine (dev/testing), falls back to a placeholder image.
"""

import io
import logging
import threading
import time
from pathlib import Path

logger = logging.getLogger(__name__)

# Attempt to import picamera2 — only available on Pi
try:
    from picamera2 import Picamera2
    from libcamera import controls as libcamera_controls
    PI_CAMERA = True
except ImportError:
    PI_CAMERA = False
    logger.warning("picamera2 not found — using dev/fallback camera mode")


class _DevCamera:
    """Minimal stand-in camera for development on non-Pi hardware.
    Returns a static placeholder JPEG so the UI and API still work.
    """

    PLACEHOLDER = Path(__file__).parent / "placeholder.jpg"

    def start(self):
        pass

    def stop(self):
        pass

    def get_frame(self) -> bytes | None:
        if self.PLACEHOLDER.exists():
            return self.PLACEHOLDER.read_bytes()
        # Generate a tiny grey JPEG on the fly if no placeholder file exists
        try:
            from PIL import Image
            img = Image.new("RGB", (640, 480), color=(180, 180, 180))
            buf = io.BytesIO()
            img.save(buf, format="JPEG")
            return buf.getvalue()
        except ImportError:
            return None

    def set_zoom(self, factor: float) -> None:
        pass  # No-op in dev mode


class _PiCamera:
    """Pi camera using picamera2 with a circular MJPEG frame buffer."""

    def __init__(self):
        self._cam: Picamera2 | None = None
        self._frame: bytes | None = None
        self._lock = threading.Lock()
        self._running = False
        self._thread: threading.Thread | None = None

    def start(self):
        self._cam = Picamera2()
        config = self._cam.create_video_configuration(
            main={"size": (1280, 960), "format": "RGB888"},
            lores={"size": (640, 480), "format": "YUV420"},
            display="lores",
        )
        self._cam.configure(config)
        self._cam.start()

        # Enable continuous autofocus (Camera Module 3 only — silently ignored on older modules)
        try:
            self._cam.set_controls({"AfMode": libcamera_controls.AfModeEnum.Continuous})
            logger.info("Continuous autofocus enabled")
        except Exception:
            logger.info("Autofocus not available on this camera module — skipping")

        self._running = True
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()
        logger.info("Pi camera started")

    def stop(self):
        self._running = False
        if self._cam:
            self._cam.stop()
            self._cam.close()

    def _capture_loop(self):
        """Continuously capture JPEG frames into the frame buffer."""
        while self._running:
            buf = io.BytesIO()
            self._cam.capture_file(buf, format="jpeg")
            with self._lock:
                self._frame = buf.getvalue()
            time.sleep(0.05)  # ~20 fps preview

    def get_frame(self) -> bytes | None:
        with self._lock:
            return self._frame

    def set_zoom(self, factor: float) -> None:
        """Adjust zoom by cropping the sensor area.
        factor=1.0 is fully zoomed out (entire sensor), factor=4.0 is 4x zoom.
        """
        factor = max(1.0, min(factor, 4.0))
        try:
            sensor_w, sensor_h = self._cam.camera_properties["PixelArraySize"]
            crop_w = int(sensor_w / factor)
            crop_h = int(sensor_h / factor)
            crop_x = (sensor_w - crop_w) // 2
            crop_y = (sensor_h - crop_h) // 2
            self._cam.set_controls({"ScalerCrop": (crop_x, crop_y, crop_w, crop_h)})
            logger.info("Zoom set to %.2fx (crop %dx%d)", factor, crop_w, crop_h)
        except Exception as exc:
            logger.warning("Failed to set zoom: %s", exc)


class Camera:
    """Public camera interface — automatically selects Pi or dev backend."""

    def __init__(self):
        self._backend = _PiCamera() if PI_CAMERA else _DevCamera()

    def start(self):
        self._backend.start()

    def stop(self):
        self._backend.stop()

    def get_frame(self) -> bytes | None:
        return self._backend.get_frame()

    def set_zoom(self, factor: float) -> None:
        self._backend.set_zoom(factor)
