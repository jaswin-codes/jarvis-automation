import cv2
import time

print("=== JARVIS - Face Check Test ===\n")

# ── Load OpenCV's built-in face detector ──────────────────────────────────────
# This xml file comes bundled with opencv, no download needed
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

# ── Camera settings ───────────────────────────────────────────────────────────
CAMERA_INDEX  = 0      # 0 = default webcam, change if you have multiple
CHECK_FRAMES  = 10      # how many frames to sample before deciding
SCALE_FACTOR  = 1.1    # how much image is scaled between detections
MIN_NEIGHBORS = 6      # higher = stricter, fewer false positives
MIN_SIZE      = (60, 60) # minimum face size to detect in pixels

# ─────────────────────────────────────────────────────────────────────────────
def check_face_present():
    """
    Opens camera briefly, samples CHECK_FRAMES frames,
    returns True if face detected in at least 2 frames.
    More reliable than single frame detection.
    """
    cap = cv2.VideoCapture(CAMERA_INDEX)

    if not cap.isOpened():
        print("⚠️  Could not open camera!")
        return False

    time.sleep(0.3)

    face_count  = 0   # how many frames had a face
    frame_count = 0
    CONFIRM_FRAMES = 2  # need face in this many frames to confirm

    while frame_count < CHECK_FRAMES:
        ret, frame = cap.read()

        if not ret:
            print("⚠️  Could not read frame!")
            break

        grey = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Equalise histogram — improves detection in bad lighting
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
            print(f"  [frame {frame_count}: ✅ face detected — confirmed {face_count}/{CONFIRM_FRAMES}]")

            # Only confirm if seen in multiple frames
            if face_count >= CONFIRM_FRAMES:
                cap.release()
                return True
        else:
            print(f"  [frame {frame_count}: ❌ no face]")

    cap.release()
    return False

# ─────────────────────────────────────────────────────────────────────────────
def run_test():
    """Run multiple face check tests interactively."""
    print("This will check for your face before allowing any action.")
    print("Testing 5 scenarios — follow the instructions.\n")

    scenarios = [
        ("Sit normally in front of camera",           True),
        ("Move slightly to the side",                 True),
        ("Cover your face with your hand",            False),
        ("Look away from camera",                     False),
        ("Sit normally again",                        True),
    ]

    passed = 0
    failed = 0

    for i, (instruction, expect_face) in enumerate(scenarios, 1):
        print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"Test {i}/5: {instruction}")
        input("   Press Enter when ready...")

        print("   📷 Checking camera...\n")
        result = check_face_present()

        if result:
            print(f"\n   🟢 Face detected → command ALLOWED")
        else:
            print(f"\n   🔴 No face → command BLOCKED")
            print(f"   → Jarvis would say: 'Unauthorized user detected.'")

        # Check if result matches expectation
        if result == expect_face:
            print(f"   ✅ Correct behaviour!\n")
            passed += 1
        else:
            if expect_face:
                print(f"   ⚠️  Should have detected face — try adjusting lighting\n")
            else:
                print(f"   ⚠️  Should have blocked — try stricter MIN_NEIGHBORS\n")
            failed += 1

        time.sleep(0.5)

    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"\n📊 Results: {passed}/5 correct")

    if passed == 5:
        print("✅ Face check working perfectly!")
    elif passed >= 3:
        print("⚠️  Mostly working — may need lighting/threshold tweaks.")
    else:
        print("❌ Needs tuning — check lighting and camera angle.")

# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    run_test()