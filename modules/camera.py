import cv2
import threading
import time

# ── Settings ──────────────────────────────────────────────────────────────────
CAMERA_INDEX = 0
WIDTH, HEIGHT = 640, 480

# ─────────────────────────────────────────────────────────────────────────────
class SharedCamera:
    """
    Owns the webcam in one background thread and keeps the latest frame.
    Windows usually lets only one VideoCapture open a camera at a time,
    so the face monitor and gesture detector both read from here.
    """
    def __init__(self, index=CAMERA_INDEX):
        self.index    = index
        self._frame   = None
        self._lock    = threading.Lock()
        self._running = False

    def start(self):
        self._running = True
        threading.Thread(target=self._capture_loop, daemon=True).start()
        print("✅ Shared camera started (background)")

    def stop(self):
        self._running = False

    def read(self):
        """Latest frame (a copy), or None if the camera isn't ready."""
        with self._lock:
            return None if self._frame is None else self._frame.copy()

    def _capture_loop(self):
        # DirectShow: the default MSMF backend takes ~13s per open/resize here and can stall
        cap = cv2.VideoCapture(self.index, cv2.CAP_DSHOW)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
        if not cap.isOpened():
            print("⚠️  Could not open camera!")
            return

        while self._running:
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.1)
                continue
            with self._lock:
                self._frame = frame

        cap.release()
