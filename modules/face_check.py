import cv2
import time

# ── Settings ──────────────────────────────────────────────────────────────────
CAMERA_INDEX   = 0
CHECK_FRAMES   = 10
SCALE_FACTOR   = 1.1
MIN_NEIGHBORS  = 6
MIN_SIZE       = (60, 60)
CONFIRM_FRAMES = 2

# ── Load classifier once at import ────────────────────────────────────────────
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

# ─────────────────────────────────────────────────────────────────────────────
def check_face_present():
    """
    Opens camera briefly, samples CHECK_FRAMES frames.
    Returns True if face confirmed in at least CONFIRM_FRAMES frames.
    """
    cap = cv2.VideoCapture(CAMERA_INDEX)

    if not cap.isOpened():
        print("⚠️  Could not open camera!")
        return False

    time.sleep(0.3)

    face_count  = 0
    frame_count = 0

    while frame_count < CHECK_FRAMES:
        ret, frame = cap.read()
        if not ret:
            break

        grey = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        grey = cv2.equalizeHist(grey)

        faces = face_cascade.detectMultiScale(
            grey,
            scaleFactor  = SCALE_FACTOR,
            minNeighbors = MIN_NEIGHBORS,
            minSize      = MIN_SIZE
        )

        frame_count += 1

        if len(faces) > 0:
            face_count += 1
            if face_count >= CONFIRM_FRAMES:
                cap.release()
                time.sleep(0.5)  # release window for other camera users
                return True

    cap.release()
    time.sleep(0.5)  # release window for other camera users
    return False

# ─────────────────────────────────────────────────────────────────────────────
class BackgroundFaceMonitor:
    """
    Runs continuous face detection in background.
    Updates face_present and mode flags automatically.
    Used by main.py to switch between desk and proximity mode.
    """
    def __init__(self, check_interval=3.0):
        self.check_interval = check_interval
        self.face_present   = False
        self.mode           = "proximity"  # "desk" or "proximity"
        self._running       = False
        self._thread        = None

    def start(self):
        import threading
        self._running = True
        self._thread  = threading.Thread(
            target=self._monitor_loop,
            daemon=True
        )
        self._thread.start()
        print("✅ Face monitor started (background)")

    def stop(self):
        self._running = False

    def _monitor_loop(self):
        while self._running:
            self.face_present = check_face_present()
            self.mode = "desk" if self.face_present else "proximity"
            print(f"  [face monitor: {self.mode} mode]")
            time.sleep(self.check_interval)

    @property
    def is_desk_mode(self):
        return self.mode == "desk"

    @property
    def is_proximity_mode(self):
        return self.mode == "proximity"