import os
import threading
import time
from collections import deque

import cv2

# ── Settings ──────────────────────────────────────────────────────────────────
MODEL_FILE        = "assets/hand_landmarker.task"
MODEL_URL         = ("https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
                     "hand_landmarker/float16/latest/hand_landmarker.task")
FPS               = 15
BUFFER_FRAMES     = 8   # ~0.5 s at 15 fps
CONFIRM_FRAMES    = 6   # frames in the buffer that must agree

# ── Hand poses: [thumb, index, middle, ring, pinky], 1 = up, -1 = ignore ──────
# The thumb is the least reliable finger, so most poses ignore it.
GESTURES = {
    "gesture_point": [-1, 1, 0, 0, 0],
    "gesture_peace": [-1, 1, 1, 0, 0],
    "gesture_three": [-1, 1, 1, 1, 0],
    "gesture_rock" : [-1, 1, 0, 0, 1],
    "gesture_palm" : [ 1, 1, 1, 1, 1],
}

# ─────────────────────────────────────────────────────────────────────────────
def finger_states(points):
    """
    points: 21 (x, y) hand landmarks, y grows downwards.
    Returns [thumb, index, middle, ring, pinky] with 1 = up (from jutsu_code).
    """
    if len(points) < 21:
        return [0, 0, 0, 0, 0]

    # Thumb: compare its tip with the base of the index finger, on the side
    # away from the wrist, so it works for either hand
    thumb_x, anchor_x, wrist_x = points[4][0], points[5][0], points[0][0]
    if wrist_x < anchor_x:
        fingers = [1 if thumb_x > anchor_x else 0]
    else:
        fingers = [1 if thumb_x < anchor_x else 0]

    # Other fingers: tip above the middle joint means up
    for tip, joint in zip([8, 12, 16, 20], [6, 10, 14, 18]):
        fingers.append(1 if points[tip][1] < points[joint][1] else 0)
    return fingers

# ─────────────────────────────────────────────────────────────────────────────
def match_gesture(fingers):
    for name, pattern in GESTURES.items():
        if all(p == -1 or p == f for p, f in zip(pattern, fingers)):
            return name
    return None

# ─────────────────────────────────────────────────────────────────────────────
class GestureTrigger:
    """
    Smooths per-frame guesses and fires once per held pose.
    The pose has to be dropped (or changed) before it can fire again.
    """
    def __init__(self, buffer_frames=BUFFER_FRAMES, confirm_frames=CONFIRM_FRAMES):
        self.buffer         = deque(maxlen=buffer_frames)
        self.confirm_frames = confirm_frames
        self.last_fired     = None

    def update(self, gesture):
        """Feed one frame's gesture (or None). Returns a gesture to fire, or None."""
        self.buffer.append(gesture)
        stable = None
        for g in set(self.buffer) - {None}:
            if self.buffer.count(g) >= self.confirm_frames:
                stable = g
        if self.buffer.count(None) >= self.confirm_frames:
            self.last_fired = None   # hand dropped: allow the next pose
        if stable and stable != self.last_fired:
            self.last_fired = stable
            return stable
        return None

# ─────────────────────────────────────────────────────────────────────────────
class GestureDetector:
    """
    Reads frames from the shared camera, finds one hand with MediaPipe,
    and calls on_detected(gesture_name) when a pose is held.
    """
    def __init__(self, camera, on_detected):
        self.camera      = camera
        self.on_detected = on_detected
        self._running    = False

    def start(self):
        if not os.path.exists(MODEL_FILE):
            print(f"⚠️  Gestures off: download the hand model to {MODEL_FILE}")
            print(f"   from {MODEL_URL}")
            return
        try:
            import mediapipe  # noqa: F401  (heavy import, only when gestures are on)
        except ImportError:
            print("⚠️  Gestures off: mediapipe is not installed (pip install -r requirements.txt)")
            return
        self._running = True
        threading.Thread(target=self._detect_loop, daemon=True).start()
        print("✅ Gesture detector started (background)")

    def stop(self):
        self._running = False

    def _detect_loop(self):
        import mediapipe as mp

        options = mp.tasks.vision.HandLandmarkerOptions(
            base_options = mp.tasks.BaseOptions(model_asset_path=MODEL_FILE),
            running_mode = mp.tasks.vision.RunningMode.VIDEO,
            num_hands    = 1,
            min_hand_detection_confidence = 0.7,
            min_tracking_confidence       = 0.7,
        )
        trigger = GestureTrigger()

        with mp.tasks.vision.HandLandmarker.create_from_options(options) as landmarker:
            while self._running:
                time.sleep(1 / FPS)
                frame = self.camera.read()
                if frame is None:
                    continue

                rgb    = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                image  = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
                result = landmarker.detect_for_video(image, int(time.monotonic() * 1000))

                gesture = None
                if result.hand_landmarks:
                    points  = [(lm.x, lm.y) for lm in result.hand_landmarks[0]]
                    gesture = match_gesture(finger_states(points))

                fired = trigger.update(gesture)
                if fired:
                    print(f"✋ Gesture: {fired}")
                    self.on_detected(fired)
