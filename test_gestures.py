# Run: python test_gestures.py  (no camera or mediapipe needed)
from modules.gesture_detector import finger_states, match_gesture, GestureTrigger

def hand(up):
    """Fake 21 landmarks for a right hand (wrist left of the index base). up = 5 flags."""
    pts = [(0.5, 0.9)] * 21
    pts[0], pts[5] = (0.40, 0.90), (0.50, 0.60)          # wrist, index base
    pts[4] = (0.60, 0.60) if up[0] else (0.45, 0.65)     # thumb tip beyond / inside the anchor
    for i, (tip, joint) in enumerate(zip([8, 12, 16, 20], [6, 10, 14, 18])):
        pts[joint] = (0.5, 0.50)
        pts[tip]   = (0.5, 0.30 if up[i + 1] else 0.70)
    return pts

assert finger_states(hand([1, 1, 1, 1, 1])) == [1, 1, 1, 1, 1]
assert finger_states(hand([0, 1, 0, 0, 1])) == [0, 1, 0, 0, 1]
assert finger_states([]) == [0, 0, 0, 0, 0]

assert match_gesture([0, 1, 0, 0, 0]) == "gesture_point"
assert match_gesture([1, 1, 1, 0, 0]) == "gesture_peace"   # thumb ignored
assert match_gesture([0, 1, 1, 1, 0]) == "gesture_three"
assert match_gesture([1, 1, 0, 0, 1]) == "gesture_rock"
assert match_gesture([1, 1, 1, 1, 1]) == "gesture_palm"
assert match_gesture([0, 1, 1, 1, 1]) is None               # four fingers: nothing
assert match_gesture([0, 0, 0, 0, 0]) is None               # fist: nothing

# Fires once when a pose is held, not on every frame
t = GestureTrigger(buffer_frames=8, confirm_frames=6)
fired = [t.update("gesture_peace") for _ in range(30)]
assert fired.count("gesture_peace") == 1

# A one-frame flicker doesn't re-fire; dropping the hand then re-posing does
assert t.update(None) is None and t.update("gesture_peace") is None
for _ in range(8):
    t.update(None)
assert [t.update("gesture_peace") for _ in range(8)].count("gesture_peace") == 1

# Switching straight to another pose fires the new one
assert "gesture_three" in [t.update("gesture_three") for _ in range(8)]

# Face check reads the shared camera instead of opening its own
import numpy as np
from modules.face_check import check_face_present

class FakeCamera:
    def __init__(self, frame): self.frame = frame
    def read(self): return self.frame

assert check_face_present(FakeCamera(np.zeros((480, 640, 3), np.uint8))) is False
assert check_face_present(FakeCamera(None)) is False

print("✅ test_gestures passed")
