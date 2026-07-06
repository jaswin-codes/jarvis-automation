import pyaudio
import wave
import numpy as np
import os
from resemblyzer import VoiceEncoder, preprocess_wav
from pathlib import Path

# ── Settings ──────────────────────────────────────────────────────────────────
SAMPLE_RATE     = 16000
CHANNELS        = 1
CHUNK           = 1024
RECORD_SECONDS  = 4
VOICEPRINT_FILE = "assets/voiceprint.npy"
TEMP_WAV        = "assets/temp_verify.wav"
THRESHOLD       = 0.75

# ── Load encoder and voiceprint once at import time ───────────────────────────
print("⏳ Loading voice authentication model...")
_encoder    = VoiceEncoder()
_voiceprint = np.load(VOICEPRINT_FILE)
print("✅ Voice authentication ready!")

p = pyaudio.PyAudio()

# ─────────────────────────────────────────────────────────────────────────────
def record_clip(seconds=RECORD_SECONDS):
    """Record a short audio clip and save to temp file."""
    stream = p.open(
        format=pyaudio.paInt16,
        channels=CHANNELS,
        rate=SAMPLE_RATE,
        input=True,
        frames_per_buffer=CHUNK
    )

    frames = []
    for _ in range(0, int(SAMPLE_RATE / CHUNK * seconds)):
        data = stream.read(CHUNK, exception_on_overflow=False)
        frames.append(data)

    stream.stop_stream()
    stream.close()

    wf = wave.open(TEMP_WAV, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
    wf.setframerate(SAMPLE_RATE)
    wf.writeframes(b''.join(frames))
    wf.close()

# ─────────────────────────────────────────────────────────────────────────────
def verify_from_file(wav_path):
    """
    Verify if a given wav file matches the saved voiceprint.
    Returns (is_match, similarity_score)
    """
    try:
        wav        = preprocess_wav(Path(wav_path))
        embedding  = _encoder.embed_utterance(wav)
        similarity = float(np.dot(embedding, _voiceprint) / (
            np.linalg.norm(embedding) * np.linalg.norm(_voiceprint)
        ))
        is_match = similarity >= THRESHOLD
        return is_match, similarity
    except Exception as e:
        print(f"⚠️  Voice auth error: {e}")
        return False, 0.0

# ─────────────────────────────────────────────────────────────────────────────
def verify_voice(audio_data=None):
    """
    Main verification function.
    If audio_data (numpy array) provided, saves it and verifies.
    Otherwise records a fresh clip then verifies.
    Returns (is_match, similarity_score)
    """
    if audio_data is not None:
        # Save provided audio data to temp file
        wf = wave.open(TEMP_WAV, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)  # 16-bit = 2 bytes
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio_data.tobytes())
        wf.close()
    else:
        record_clip()

    is_match, score = verify_from_file(TEMP_WAV)

    if os.path.exists(TEMP_WAV):
        os.remove(TEMP_WAV)

    return is_match, score

# ─────────────────────────────────────────────────────────────────────────────
def cleanup():
    """Call when shutting down."""
    p.terminate()
    if os.path.exists(TEMP_WAV):
        os.remove(TEMP_WAV)