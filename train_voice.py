import pyaudio
import wave
import numpy as np
import os
import time
from resemblyzer import VoiceEncoder, preprocess_wav
from pathlib import Path

print("=== JARVIS - Voice Authentication Training ===\n")

# ── Settings ──────────────────────────────────────────────────────────────────
SAMPLE_RATE    = 16000
CHANNELS       = 1
CHUNK          = 1024
RECORD_SECONDS = 5
NUM_SAMPLES    = 8       # record 8 phrases for a robust voiceprint
OUTPUT_DIR     = "assets/voice_training"
VOICEPRINT_FILE = "assets/voiceprint.npy"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Phrases to say during training ───────────────────────────────────────────
# Varied phrases give a more robust voiceprint than repeating the same thing
PHRASES = [
    "Hey Jarvis, systems online",
    "Jarvis lock the workstation",
    "Open Amathuba now",
    "Jarvis initiate sleep mode",
    "Volume up please Jarvis",
    "Hey Jarvis take a screenshot",
    "Jarvis open the browser",
    "Systems activate voice recognition",
]

p = pyaudio.PyAudio()

# ─────────────────────────────────────────────────────────────────────────────
def record_sample(filename, phrase, index):
    """Record a single voice sample."""
    print(f"\n[{index}/{NUM_SAMPLES}] Say this phrase:")
    print(f'   "{phrase}"')
    print("   Recording in 3 seconds...")

    for i in range(3, 0, -1):
        print(f"   {i}...")
        time.sleep(1)

    print("   ▶ SPEAK NOW!\n")

    stream = p.open(
        format=pyaudio.paInt16,
        channels=CHANNELS,
        rate=SAMPLE_RATE,
        input=True,
        frames_per_buffer=CHUNK
    )

    frames = []
    for _ in range(0, int(SAMPLE_RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK, exception_on_overflow=False)
        frames.append(data)

    stream.stop_stream()
    stream.close()
    print("   ✅ Recorded!")

    # Save as wav
    path = os.path.join(OUTPUT_DIR, filename)
    wf = wave.open(path, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
    wf.setframerate(SAMPLE_RATE)
    wf.writeframes(b''.join(frames))
    wf.close()

    return path

# ─────────────────────────────────────────────────────────────────────────────
def build_voiceprint(wav_paths):
    """
    Load all recorded samples, extract embeddings,
    and average them into a single voiceprint.
    """
    print("\n⏳ Loading voice encoder model...")
    encoder = VoiceEncoder()
    print("✅ Model loaded!\n")

    embeddings = []

    for i, path in enumerate(wav_paths, 1):
        print(f"  Processing sample {i}/{len(wav_paths)}: {path}")
        try:
            wav = preprocess_wav(Path(path))
            embedding = encoder.embed_utterance(wav)
            embeddings.append(embedding)
            print(f"  ✅ Processed")
        except Exception as e:
            print(f"  ⚠️  Skipped ({e})")

    if not embeddings:
        print("❌ No embeddings generated — check your recordings!")
        return None

    # Average all embeddings into one voiceprint
    voiceprint = np.mean(embeddings, axis=0)
    return voiceprint

# ─────────────────────────────────────────────────────────────────────────────
def main():
    print("This will record 8 short phrases to build your voiceprint.")
    print("Speak clearly and at a normal volume.\n")
    print("━" * 45)

    wav_paths = []

    # ── Record all samples ────────────────────────────────────────────────────
    for i, phrase in enumerate(PHRASES, 1):
        filename = f"sample_{i}.wav"
        path = record_sample(filename, phrase, i)
        wav_paths.append(path)
        time.sleep(0.5)

    print("\n━" * 45)
    print("✅ All samples recorded!")

    # ── Build voiceprint ──────────────────────────────────────────────────────
    print("\n⏳ Building your voiceprint from recordings...")
    voiceprint = build_voiceprint(wav_paths)

    if voiceprint is not None:
        np.save(VOICEPRINT_FILE, voiceprint)
        print(f"\n✅ Voiceprint saved to: {VOICEPRINT_FILE}")
        print(f"   Shape: {voiceprint.shape}")
        print("\n🎉 Training complete! Run test_voice_auth.py to verify.")
    else:
        print("\n❌ Training failed — please try again.")

    p.terminate()

if __name__ == "__main__":
    main()