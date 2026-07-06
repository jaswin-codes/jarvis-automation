import pyaudio
import numpy as np
from openwakeword.model import Model
import speech_recognition as sr
import time
import threading

print("=== JARVIS - Wake Word + Voice Command Test ===")
print("⏳ Loading wake word model...\n")

# ── Load wake word model ──────────────────────────────────────────────────────
oww_model = Model(
    wakeword_models=["hey_jarvis"],
    inference_framework="onnx"
)

print("✅ Model loaded!")
print("🎙️  Say 'Hey Jarvis' then a command:")
print("   'jarvis lock'")
print("   'jarvis sleep'")
print("   'jarvis open amathuba'")
print("   'jarvis open browser'")
print("   'jarvis volume up'")
print("   'jarvis volume down'")
print("   'jarvis screenshot'")
print("   'jarvis shutdown'")
print("   'jarvis stop'  ← disarms the system")
print("\n   Press Ctrl+C to quit.\n")

# ── Audio settings ────────────────────────────────────────────────────────────
SAMPLE_RATE = 16000
CHUNK       = 1280
FORMAT      = pyaudio.paInt16

# ── Detection settings ────────────────────────────────────────────────────────
THRESHOLD = 0.5
COOLDOWN  = 3.0

# ── State ─────────────────────────────────────────────────────────────────────
system_armed    = False
last_trigger    = 0
listening_cmd   = False   # True when actively listening for a command

# ── Speech recogniser ─────────────────────────────────────────────────────────
recogniser = sr.Recognizer()
recogniser.energy_threshold    = 300   # mic sensitivity
recogniser.pause_threshold     = 0.5   # seconds of silence = end of command
recogniser.dynamic_energy_threshold = True

# ─────────────────────────────────────────────────────────────────────────────
# Command map — what to do for each phrase
# ─────────────────────────────────────────────────────────────────────────────
COMMAND_MAP = {
    "lock"            : "locking",
    "jarvis lock"     : "locking",
    "sleep"           : "sleeping",
    "jarvis sleep"    : "sleeping",
    "open amathuba"   : "opening_amathuba",
    "jarvis open amathuba": "opening_amathuba",
    "open browser"    : "double_clap",
    "jarvis open browser": "double_clap",
    "volume up"       : "volume_up",
    "jarvis volume up": "volume_up",
    "volume down"     : "volume_down",
    "jarvis volume down": "volume_down",
    "screenshot"      : "screenshot",
    "jarvis screenshot": "screenshot",
    "shutdown"        : "shutdown",
    "jarvis shutdown" : "shutdown",
    "stop"            : "disarmed",
    "jarvis stop"     : "disarmed",
    "deactivate"      : "disarmed",
    "jarvis deactivate": "disarmed",
}

# ─────────────────────────────────────────────────────────────────────────────
def match_command(text):
    """
    Try to match spoken text to a command.
    Checks exact matches first, then partial matches.
    """
    text = text.lower().strip()
    print(f"  [heard: '{text}']")

    # Exact match
    if text in COMMAND_MAP:
        return COMMAND_MAP[text]

    # Partial match — check if any key is contained in what was said
    for key in COMMAND_MAP:
        if key in text:
            return COMMAND_MAP[key]

    return None

# ─────────────────────────────────────────────────────────────────────────────
def listen_for_command():
    """
    Listen for a single voice command after wake word triggers.
    Runs in a separate thread so it doesn't block wake word detection.
    """
    global system_armed, listening_cmd

    print("👂 Listening for command... (speak now)\n")

    with sr.Microphone() as source:
        recogniser.adjust_for_ambient_noise(source, duration=0.1)
        try:
            # Wait up to 5 seconds for speech, then 5 seconds to finish
            audio = recogniser.listen(source, timeout=5, phrase_time_limit=5)
            text  = recogniser.recognize_google(audio)

            action = match_command(text)

            if action:
                if action == "disarmed":
                    print("🔴 Jarvis disarmed. Say 'Hey Jarvis' to reactivate.\n")
                    system_armed = False
                else:
                    print(f"✅ Command recognised → action: '{action}'")
                    print(f"   → Would now execute: {action}\n")
            else:
                print("❓ Command not recognised. Try again.\n")

        except sr.WaitTimeoutError:
            print("⏱️  No command heard — going back to standby.\n")
        except sr.UnknownValueError:
            print("❓ Could not understand audio. Try again.\n")
        except sr.RequestError as e:
            print(f"⚠️  Speech recognition error: {e}\n")

    listening_cmd = False

# ─────────────────────────────────────────────────────────────────────────────
p = pyaudio.PyAudio()

stream = p.open(
    format=FORMAT,
    channels=1,
    rate=SAMPLE_RATE,
    input=True,
    frames_per_buffer=CHUNK
)

# ── Main loop ─────────────────────────────────────────────────────────────────
try:
    while True:
        audio_chunk = stream.read(CHUNK, exception_on_overflow=False)
        audio_np    = np.frombuffer(audio_chunk, dtype=np.int16)
        prediction  = oww_model.predict(audio_np)
        score       = prediction.get("hey_jarvis", 0)
        now         = time.time()

        # ── Wake word detected ────────────────────────────────────────────────
        if score >= THRESHOLD and (now - last_trigger) >= COOLDOWN:
            last_trigger = now
            system_armed = True
            print(f"🟢 WAKE WORD DETECTED! (confidence: {score:.2f})")
            print("   → Jarvis armed. Awaiting command...\n")

            # Listen for command in a separate thread
            # so wake word stream keeps running
            if not listening_cmd:
                listening_cmd = True
                cmd_thread = threading.Thread(
                    target=listen_for_command,
                    daemon=True
                )
                cmd_thread.start()

except KeyboardInterrupt:
    print("\n🛑 Stopped.")
    stream.stop_stream()
    stream.close()
    p.terminate()