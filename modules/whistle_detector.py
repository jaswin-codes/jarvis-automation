import pyaudio
import numpy as np
import threading
import time

# ── Settings ──────────────────────────────────────────────────────────────────
SAMPLE_RATE   = 44100
CHUNK         = 2048
WHISTLE_LOW   = 1000
WHISTLE_HIGH  = 3500
ENERGY_THRESH = 0.01
RATIO_THRESH  = 0.55
SHORT_MIN     = 0.4
SHORT_MAX     = 1.2
LONG_MIN      = 1.2
SILENCE_GAP   = 0.5

# ─────────────────────────────────────────────────────────────────────────────
def _is_whistle(audio_chunk):
    data = np.frombuffer(audio_chunk, dtype=np.int16).astype(np.float32)
    data /= 32768.0
    energy = np.sqrt(np.mean(data**2))
    if energy < ENERGY_THRESH:
        return False

    fft   = np.abs(np.fft.rfft(data))
    freqs = np.fft.rfftfreq(len(data), 1.0 / SAMPLE_RATE)

    total_energy   = np.sum(fft)
    whistle_mask   = (freqs >= WHISTLE_LOW) & (freqs <= WHISTLE_HIGH)
    whistle_energy = np.sum(fft[whistle_mask])
    ratio          = whistle_energy / total_energy if total_energy > 0 else 0

    return ratio >= RATIO_THRESH

# ─────────────────────────────────────────────────────────────────────────────
class WhistleDetector:
    """
    Continuously listens for whistles in background thread.
    Calls on_detected("short_whistle") or on_detected("long_whistle").
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
        print("✅ Whistle detector started (background)")

    def stop(self):
        self._running = False

    def _listen_loop(self):
        p      = pyaudio.PyAudio()
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=SAMPLE_RATE,
            input=True,
            frames_per_buffer=CHUNK
        )

        whistle_start     = None
        last_whistle_time = None
        in_whistle        = False

        while self._running:
            try:
                chunk    = stream.read(CHUNK, exception_on_overflow=False)
                detected = _is_whistle(chunk)
                now      = time.time()

                if detected:
                    if not in_whistle:
                        whistle_start = now
                        in_whistle    = True
                    last_whistle_time = now

                if in_whistle and last_whistle_time and \
                        (now - last_whistle_time) >= SILENCE_GAP:
                    duration = last_whistle_time - whistle_start

                    if SHORT_MIN <= duration < SHORT_MAX:
                        print(f"🎵 Short whistle ({duration:.2f}s)")
                        self.on_detected("short_whistle")
                    elif duration >= LONG_MIN:
                        print(f"🎵🎵 Long whistle ({duration:.2f}s)")
                        self.on_detected("long_whistle")

                    whistle_start     = None
                    last_whistle_time = None
                    in_whistle        = False

            except Exception as e:
                print(f"⚠️  Whistle error: {e}")

        stream.stop_stream()
        stream.close()
        p.terminate()