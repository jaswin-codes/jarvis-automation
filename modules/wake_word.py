import pyaudio
import numpy as np
from openwakeword.model import Model
import threading
import time

# ── Settings ──────────────────────────────────────────────────────────────────
SAMPLE_RATE = 16000
CHUNK       = 1280
FORMAT      = pyaudio.paInt16
THRESHOLD   = 0.5
COOLDOWN    = 3.0

# ─────────────────────────────────────────────────────────────────────────────
class WakeWordDetector:
    """
    Continuously listens for 'Hey Jarvis' in background thread.
    Calls on_detected callback when wake word is heard.
    """
    def __init__(self, on_detected):
        self.on_detected = on_detected
        self._running    = False
        self._thread     = None
        self._last_trigger = 0

        print("⏳ Loading wake word model...")
        self.model = Model(
            wakeword_models    = ["hey_jarvis"],
            inference_framework= "onnx"
        )
        print("✅ Wake word model loaded!")

    def start(self):
        self._running = True
        self._thread  = threading.Thread(
            target=self._listen_loop,
            daemon=True
        )
        self._thread.start()
        print("✅ Wake word detector started (background)")

    def stop(self):
        self._running = False

    def _listen_loop(self):
        p = pyaudio.PyAudio()
        stream = p.open(
            format=FORMAT,
            channels=1,
            rate=SAMPLE_RATE,
            input=True,
            frames_per_buffer=CHUNK
        )

        while self._running:
            try:
                chunk    = stream.read(CHUNK, exception_on_overflow=False)
                audio_np = np.frombuffer(chunk, dtype=np.int16)
                pred     = self.model.predict(audio_np)
                score    = pred.get("hey_jarvis", 0)
                now      = time.time()

                if score >= THRESHOLD and (now - self._last_trigger) >= COOLDOWN:
                    self._last_trigger = now
                    print(f"🟢 Wake word detected! (confidence: {score:.2f})")
                    self.on_detected()

            except Exception as e:
                print(f"⚠️  Wake word error: {e}")

        stream.stop_stream()
        stream.close()
        p.terminate()