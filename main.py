import time
import threading
import json
import os
import speech_recognition as sr
import numpy as np

from modules.voice         import speak, cleanup as voice_cleanup
from modules.voice_auth    import verify_voice
from modules.face_check    import BackgroundFaceMonitor
from modules.wake_word     import WakeWordDetector
from modules.clap_detector import ClapSnapDetector
from modules.whistle_detector import WhistleDetector
from modules.gesture_detector import GestureDetector
from modules.camera        import SharedCamera
from modules.actions       import execute
from modules.tasks         import route_task

print("=" * 55)
print("         J.A.R.V.I.S  —  Starting up")
print("=" * 55)

# ── Load config ───────────────────────────────────────────────────────────────
with open("config.json", "r") as f:
    config = json.load(f)

# ── Global state ──────────────────────────────────────────────────────────────
system_armed     = False   # True after wake word detected
listening_cmd    = False   # True while listening for voice command
silent_mode      = False   # True = no Jarvis voice responses
cooldown_active  = False
jarvis_speaking  = False
_speak_lock      = threading.Lock()
voice_cancelled = False
task_active      = False   # True while listening for a spoken Claude task
last_action_time = 0
COOLDOWN_SECS    = config.get("cooldown_seconds", 2)

# ── Speech recogniser ─────────────────────────────────────────────────────────
recogniser = sr.Recognizer()
recogniser.energy_threshold         = 300
recogniser.pause_threshold          = 0.5
recogniser.dynamic_energy_threshold = True

# ── Command map ───────────────────────────────────────────────────────────────
COMMAND_MAP = {
    "lock"                : "locking",
    "jarvis lock"         : "locking",
    "sleep"               : "sleeping",
    "jarvis sleep"        : "sleeping",
    "open amathuba"       : "opening_amathuba",
    "jarvis open amathuba": "opening_amathuba",
    "open browser"        : "open_browser",
    "jarvis open browser" : "open_browser",
    "open claude"         : "open_claude",
    "jarvis open claude"  : "open_claude",
    "open calendar"       : "open_calendar",
    "jarvis open calendar": "open_calendar",
    "volume up"           : "volume_up",
    "jarvis volume up"    : "volume_up",
    "volume down"         : "volume_down",
    "jarvis volume down"  : "volume_down",
    "screenshot"          : "screenshot",
    "jarvis screenshot"   : "screenshot",
    "shutdown"            : "shutdown",
    "jarvis shutdown"     : "shutdown",
    "silent mode"         : "silent_mode",
    "jarvis silent mode"  : "silent_mode",
    "vocal mode"          : "vocal_mode",
    "jarvis vocal mode"   : "vocal_mode",
    "stop"                : "disarmed",
    "jarvis stop"         : "disarmed",
    "deactivate"          : "disarmed",
}
MAX_COMMAND_WORDS = 4   # anything longer after "Hey Jarvis" is routed as a task

# ─────────────────────────────────────────────────────────────────────────────
def jarvis_speak(key):
    """Speak only if not in silent mode. Blocks wake word during speech."""
    global jarvis_speaking
    if not silent_mode:
        with _speak_lock:
            jarvis_speaking = True
            speak(key)
            jarvis_speaking = False
    else:
        print(f"🔇 [silent mode] would say: '{key}'")
# ─────────────────────────────────────────────────────────────────────────────
def can_trigger():
    """Check if cooldown has passed."""
    global last_action_time
    return (time.time() - last_action_time) >= COOLDOWN_SECS

# ─────────────────────────────────────────────────────────────────────────────
def trigger_action(action_key):
    """
    Central action dispatcher.
    Checks cooldown, then executes the action.
    """
    global last_action_time, system_armed, silent_mode, task_active

    # Clap/whistle/gesture triggers are remapped in config.json "triggers"
    action_key = config.get("triggers", {}).get(action_key, action_key)

    if not can_trigger():
        print(f"⏳ Cooldown active — ignoring: {action_key}")
        return

    last_action_time = time.time()

    # ── Special system actions ────────────────────────────────────────────────
    if action_key == "disarmed":
        system_armed = False
        jarvis_speak("disarmed")
        print("🔴 Jarvis disarmed\n")
        return

    if action_key == "silent_mode":
        silent_mode = True
        print("🔇 Silent mode ON")
        return

    if action_key == "vocal_mode":
        silent_mode = False
        speak("systems_online")
        print("🔊 Vocal mode ON")
        return

    if action_key == "claude_task":
        if task_active:
            return
        task_active = True
        threading.Thread(target=listen_for_task, daemon=True).start()
        return

    # ── Execute real action ───────────────────────────────────────────────────
    execute(action_key)

# ─────────────────────────────────────────────────────────────────────────────
def match_command(text):
    """Match spoken text to a command key with fuzzy fallback."""
    text = text.lower().strip()
    print(f"  [heard: '{text}']")

    # Exact match
    if text in COMMAND_MAP:
        return COMMAND_MAP[text]

    # Longer sentences are tasks, not commands: "what's my sleep schedule" mustn't sleep the laptop
    if len(text.split()) > MAX_COMMAND_WORDS:
        return None

    # Partial match
    for key in COMMAND_MAP:
        if key in text:
            return COMMAND_MAP[key]

    # ── Fuzzy fallbacks for commonly misheard words ───────────────────────────
    fuzzy_map = {
        "amity"    : "opening_amathuba",
        "mathuba"  : "opening_amathuba",
        "muthuba"  : "opening_amathuba",
        "amathuba" : "opening_amathuba",
        "lock"     : "locking",
        "sleep"    : "sleeping",
        "browser"  : "open_browser",
        "claude"   : "open_claude",
        "clawed"   : "open_claude",
        "calendar" : "open_calendar",
        "volume"   : "volume_up",
        "screenshot": "screenshot",
    }

    for fuzzy_key, action in fuzzy_map.items():
        if fuzzy_key in text:
            print(f"  [fuzzy match: '{fuzzy_key}' → '{action}']")
            return action

    return None
# ─────────────────────────────────────────────────────────────────────────────
def voice_matches(audio):
    """Check the speaker against the saved voiceprint."""
    print("🔐 Verifying voice...")
    raw_data = audio.get_raw_data(
        convert_rate  = 16000,
        convert_width = 2
    )
    audio_np        = np.frombuffer(raw_data, dtype=np.int16)
    is_match, score = verify_voice(audio_data=audio_np)
    print(f"   Voice similarity: {score:.2f}")

    if not is_match:
        print("🔴 Voice not recognised — command rejected\n")
        jarvis_speak("face_not_found")
    return is_match

# ─────────────────────────────────────────────────────────────────────────────
def listen_for_task():
    """
    Double clap → speak a task (up to 20 s) → route it to notes,
    Autobuilder or a Claude Code window.
    """
    global task_active

    try:
        jarvis_speak("task_prompt")
        print("🎙️  Listening for a task...\n")
        with sr.Microphone() as source:
            recogniser.adjust_for_ambient_noise(source, duration=0.1)
            audio = recogniser.listen(source, timeout=5, phrase_time_limit=20)

        text = recogniser.recognize_google(audio)
        print(f"  [task: '{text}']")
        if voice_matches(audio):
            jarvis_speak(route_task(text, config, say=jarvis_speak))

    except sr.WaitTimeoutError:
        print("⏱️  No task heard\n")
    except sr.UnknownValueError:
        print("❓ Could not understand the task\n")
        jarvis_speak("not_understood")
    except sr.RequestError as e:
        print(f"⚠️  Speech error: {e}\n")
    finally:
        task_active = False

# ─────────────────────────────────────────────────────────────────────────────
def listen_for_command(face_monitor):
    global system_armed, listening_cmd, voice_cancelled, task_active

    PROXIMITY_COMMANDS = {
        "locking", "sleeping", "volume_up",
        "volume_down", "shutdown", "disarmed",
        "silent_mode", "vocal_mode"
    }

    print("👂 Listening for voice command (or use clap)...\n")

    with sr.Microphone() as source:
        recogniser.adjust_for_ambient_noise(source, duration=0.1)
        try:
            audio = recogniser.listen(source, timeout=3, phrase_time_limit=12)

            # Check immediately if trigger already fired during listening
            if voice_cancelled:
                print("  [voice listener cancelled — trigger already fired]\n")
                return
            text   = recogniser.recognize_google(audio)
            action = match_command(text)
            is_desk = face_monitor.is_desk_mode

            if not action:
                # Not a known command: treat the sentence as a spoken task
                if len(text.split()) <= MAX_COMMAND_WORDS:
                    print("❓ Command not recognised\n")
                    jarvis_speak("not_understood")
                    return
                if not is_desk:
                    print("⚠️  Spoken tasks need desk mode\n")
                    return
                if voice_matches(audio):
                    task_active = True
                    try:
                        jarvis_speak(route_task(text, config, say=jarvis_speak))
                    finally:
                        task_active = False
                return

            if not is_desk and action not in PROXIMITY_COMMANDS:
                print(f"⚠️  '{action}' not available in proximity mode\n")
                return

            if not voice_matches(audio):
                return

            print(f"🟢 Voice verified! Executing: {action}\n")
            trigger_action(action)

        except sr.WaitTimeoutError:
            print("⏱️  No voice command heard — clap still active\n")
        except sr.UnknownValueError:
            print("❓ Could not understand audio\n")
        except sr.RequestError as e:
            print(f"⚠️  Speech error: {e}\n")

        finally:
            listening_cmd    = False
            system_armed     = False
            voice_cancelled  = False
            print("  [system disarmed — say Hey Jarvis to rearm]\n")

# ─────────────────────────────────────────────────────────────────────────────
# ── Callback: wake word detected ─────────────────────────────────────────────
def on_wake_word():
    global system_armed, listening_cmd

    if jarvis_speaking or listening_cmd or task_active:
        print("  [wake word ignored — system busy]")
        return

    if system_armed:
        print("  [wake word ignored — already armed]")
        return

    system_armed = True
    jarvis_speak("armed")
    print("🟢 Jarvis armed — clap, whistle or speak a command\n")

    # ── Start voice listener in background but don't block other triggers ─────
    listening_cmd = True
    t = threading.Thread(
        target=listen_for_command,
        args=(face_monitor,),
        daemon=True
    )
    t.start()
# ─────────────────────────────────────────────────────────────────────────────
# ── Callback: clap/snap detected ─────────────────────────────────────────────
def on_clap(count):
    global voice_cancelled
    if not face_monitor.is_desk_mode:
        print("  [clap ignored — not in desk mode]")
        return
    if not system_armed:
        print("  [clap ignored — system not armed]")
        return
    action_map = {1: "single_clap", 2: "double_clap", 3: "triple_clap"}
    action = action_map.get(count)
    if action:
        voice_cancelled = True   # cancel voice listener
        trigger_action(action)

def on_sensor_trigger(trigger_name):
    """Whistles and hand gestures: only in desk mode, after 'Hey Jarvis'."""
    global voice_cancelled
    if not face_monitor.is_desk_mode:
        print(f"  [{trigger_name} ignored — not in desk mode]")
        return
    if not system_armed:
        print(f"  [{trigger_name} ignored — system not armed]")
        return
    voice_cancelled = True
    trigger_action(trigger_name)
# ─────────────────────────────────────────────────────────────────────────────
# ── Initialise all components ─────────────────────────────────────────────────
print("\n⏳ Initialising components...\n")

# One thread owns the webcam; face and gesture checks share its frames
camera = SharedCamera()
camera.start()

# Face monitor — checks for a face every 5 seconds
face_monitor = BackgroundFaceMonitor(camera, check_interval=5.0)
face_monitor.start()

# Give face monitor one cycle to determine mode before starting
print("⏳ Waiting for face monitor first check...")
timeout = 10
elapsed = 0
while face_monitor.mode == "proximity" and elapsed < timeout:
    time.sleep(0.5)
    elapsed += 0.5
    # Check if camera actually found a face
    if face_monitor.face_present:
        break
print(f"📷 Mode: {face_monitor.mode.upper()}")

# Wake word detector
wake_detector = WakeWordDetector(on_detected=on_wake_word)
wake_detector.start()

# Clap/snap detector
clap_detector = ClapSnapDetector(on_detected=on_clap)
clap_detector.start()

# Whistle detector
whistle_detector = WhistleDetector(on_detected=on_sensor_trigger)
whistle_detector.start()

# Hand gesture detector (needs mediapipe + assets/hand_landmarker.task)
gesture_detector = GestureDetector(camera, on_detected=on_sensor_trigger)
gesture_detector.start()

# ── Startup complete ──────────────────────────────────────────────────────────
print("\n" + "=" * 55)
jarvis_speak("startup")
print("\n✅ Jarvis is running!")
print("   Say 'Hey Jarvis' to arm the system")
print("   Press Ctrl+C to shutdown\n")

# ─────────────────────────────────────────────────────────────────────────────
# ── Main loop ─────────────────────────────────────────────────────────────────
try:
    while True:
        # Print status every 30 seconds so you know it's alive
        time.sleep(30)
        mode = face_monitor.mode.upper()
        armed = "ARMED" if system_armed else "STANDBY"
        silent = " | SILENT" if silent_mode else ""
        print(f"  [status: {mode} | {armed}{silent}]")

except KeyboardInterrupt:
    print("\n\n🛑 Shutting down Jarvis...")
    
    # Stop all detectors first
    wake_detector.stop()
    clap_detector.stop()
    whistle_detector.stop()
    face_monitor.stop()

    # Speak goodbye then cleanup
    try:
        jarvis_speak("shutdown")
    except Exception:
        pass

    try:
        voice_cleanup()
    except Exception:
        pass

    print("✅ Jarvis offline. Goodbye.")
    os._exit(0)   # force clean exit — no traceback
