import time
from clapDetector import ClapDetector, printDeviceInfo

print("=== JARVIS - Clap/Snap Detector (v3) ===")

# ── Your calibrated values ────────────────────────────────────────────────────
# Clap and snap treated as the same trigger since they share frequency space
THRESHOLD = 1762   # from your calibration
LOWCUT    = 872    # from your calibration  
HIGHCUT   = 7745   # wide band — catches both claps and snaps

# ── Timing ───────────────────────────────────────────────────────────────────
SILENCE_WINDOW = 2.0   # seconds of silence before pattern is finalised

detector = ClapDetector(inputDevice=-1, logLevel=0)
detector.initAudio()

print("\n✅ Listening for claps or snaps...")
print("   1 = single | 2 = double | 3 = triple")
print("   Wait 2 seconds after your last sound to see result.")
print("   Press Ctrl+C to stop.\n")

count           = 0
last_sound_time = None
in_sequence     = False

try:
    while True:
        audio  = detector.getAudio()
        result = detector.run(
            thresholdBias=THRESHOLD,
            lowcut=LOWCUT,
            highcut=HIGHCUT,
            audioData=audio
        )

        now = time.time()

        # ── Sound detected ────────────────────────────────────────────────────
        if len(result) > 0:
            count          += len(result)
            last_sound_time = now
            in_sequence     = True
            print(f"  [sound detected — count so far: {count}]")

        # ── Silence window passed — decide pattern ────────────────────────────
        if in_sequence and last_sound_time and (now - last_sound_time) >= SILENCE_WINDOW:
            print()

            if count == 1:
                print("👏 SINGLE clap/snap → would trigger: Open Amathuba")
            elif count == 2:
                print("👏👏 DOUBLE clap/snap → would trigger: Open Browser")
            elif count >= 3:
                print("👏👏👏 TRIPLE clap/snap → would trigger: Action C")
            
            # ── Reset ─────────────────────────────────────────────────────────
            count           = 0
            last_sound_time = None
            in_sequence     = False
            print("\n✅ Listening...\n")

        time.sleep(1/60)

except KeyboardInterrupt:
    print("\n🛑 Stopped.")
    detector.stop()