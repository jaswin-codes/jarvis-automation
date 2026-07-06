from clapDetector import ClapDetector
import threading
import time

# ── Your calibrated values ────────────────────────────────────────────────────
THRESHOLD      = 1762
LOWCUT         = 872
HIGHCUT        = 7745
SILENCE_WINDOW = 2.0

# ─────────────────────────────────────────────────────────────────────────────
class ClapSnapDetector:
    """
    Continuously listens for clap/snap patterns in background thread.
    Calls on_detected(count) callback when pattern is complete.
    """
    def __init__(self, on_detected):
        self.on_detected = on_detected
        self._running    = False
        self._thread     = None

    def start(self):
        self._running = True
        self._thread  = threading.Thread(
            target=self._listen_loop,
            daemon=True
        )
        self._thread.start()
        print("✅ Clap/snap detector started (background)")

    def stop(self):
        self._running = False

    def _listen_loop(self):
        detector = ClapDetector(inputDevice=-1, logLevel=0)
        detector.initAudio()

        count           = 0
        last_sound_time = None
        in_sequence     = False

        while self._running:
            try:
                audio  = detector.getAudio()
                result = detector.run(
                    thresholdBias = THRESHOLD,
                    lowcut        = LOWCUT,
                    highcut       = HIGHCUT,
                    audioData     = audio
                )

                now = time.time()

                if len(result) > 0:
                    count          += len(result)
                    last_sound_time = now
                    in_sequence     = True

                if (in_sequence and last_sound_time and
                        (now - last_sound_time) >= SILENCE_WINDOW):
                    print(f"👏 Clap/snap pattern: {count} sound(s)")
                    self.on_detected(count)
                    count           = 0
                    last_sound_time = None
                    in_sequence     = False

                time.sleep(1/60)

            except Exception as e:
                print(f"⚠️  Clap detector error: {e}")

        detector.stop()