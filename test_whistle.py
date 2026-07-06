import pyaudio
import numpy as np
import time

print("=== JARVIS - Whistle Detector Test ===")

# ── Audio settings ────────────────────────────────────────────────────────────
SAMPLE_RATE   = 44100
CHUNK         = 2048
FORMAT        = pyaudio.paInt16

# ── Whistle detection settings ────────────────────────────────────────────────
WHISTLE_LOW   = 1000   # whistles live between 1000–3500 Hz typically
WHISTLE_HIGH  = 3500
ENERGY_THRESH = 0.01   # minimum energy to count as a whistle (not silence)
RATIO_THRESH  = 0.55   # how much of total energy must be in whistle band

# ── Timing ───────────────────────────────────────────────────────────────────
SHORT_MIN     = 0.2    # minimum seconds for a short whistle
SHORT_MAX     = 1.2    # maximum seconds for a short whistle
LONG_MIN      = 1.2    # minimum seconds for a long whistle
SILENCE_GAP   = 0.5    # seconds of silence to end a whistle

# ─────────────────────────────────────────────────────────────────────────────
p = pyaudio.PyAudio()

stream = p.open(
    format=FORMAT,
    channels=1,
    rate=SAMPLE_RATE,
    input=True,
    frames_per_buffer=CHUNK
)

print("\n✅ Listening for whistles...")
print("   Short whistle (< 1.2s) → Action D")
print("   Long  whistle (> 1.2s) → Action E")
print("   Press Ctrl+C to stop.\n")

# ─────────────────────────────────────────────────────────────────────────────
def is_whistle(audio_chunk):
    """
    Returns True if this chunk contains whistle-like sound.
    Strategy: check that most energy is concentrated in the whistle frequency band.
    """
    # Convert bytes to numpy array
    data = np.frombuffer(audio_chunk, dtype=np.int16).astype(np.float32)
    data /= 32768.0  # normalise to -1 to 1

    # Overall energy — if too quiet, ignore
    energy = np.sqrt(np.mean(data**2))
    if energy < ENERGY_THRESH:
        return False, energy

    # FFT to get frequency content
    fft    = np.abs(np.fft.rfft(data))
    freqs  = np.fft.rfftfreq(len(data), 1.0 / SAMPLE_RATE)

    # Energy in whistle band vs total energy
    total_energy   = np.sum(fft)
    whistle_mask   = (freqs >= WHISTLE_LOW) & (freqs <= WHISTLE_HIGH)
    whistle_energy = np.sum(fft[whistle_mask])

    ratio = whistle_energy / total_energy if total_energy > 0 else 0

    return ratio >= RATIO_THRESH, energy

# ─────────────────────────────────────────────────────────────────────────────
whistle_start    = None
last_whistle_time = None
in_whistle       = False

try:
    while True:
        audio_chunk = stream.read(CHUNK, exception_on_overflow=False)
        detected, energy = is_whistle(audio_chunk)
        now = time.time()

        if detected:
            if not in_whistle:
                # Whistle just started
                whistle_start     = now
                in_whistle        = True
                print(f"  [whistle started...]")
            last_whistle_time = now

        # ── Check if whistle just ended (silence gap passed) ──────────────────
        if in_whistle and last_whistle_time and (now - last_whistle_time) >= SILENCE_GAP:
            duration = last_whistle_time - whistle_start
            print(f"  [whistle ended — duration: {duration:.2f}s]\n")

            if SHORT_MIN <= duration < SHORT_MAX:
                print("🎵 SHORT whistle → would trigger: Play/Pause Music")
            elif duration >= LONG_MIN:
                print("🎵🎵 LONG whistle → would trigger: Maximise Window")
            else:
                print(f"  (too short to count — {duration:.2f}s, try again)")

            # ── Reset ─────────────────────────────────────────────────────────
            whistle_start     = None
            last_whistle_time = None
            in_whistle        = False
            print("\n✅ Listening...\n")

except KeyboardInterrupt:
    print("\n🛑 Stopped.")
    stream.stop_stream()
    stream.close()
    p.terminate()