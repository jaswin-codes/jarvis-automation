import edge_tts
import asyncio
import pygame
import os
import time
import uuid

# ── Settings ──────────────────────────────────────────────────────────────────
VOICE     = "en-GB-RyanNeural"
RATE      = "-25%"
PITCH     = "-15Hz"
TEMP_FILE = "assets/jarvis_temp.mp3"

# ── Initialise pygame ─────────────────────────────────────────────────────────
pygame.mixer.init()

# ── All Jarvis response lines ─────────────────────────────────────────────────
RESPONSES = {
    "startup"          : "Jarvis online. All systems nominal.",
    "systems_online"   : "Systems online. Awaiting your command.",
    "standing_by"      : "Jarvis standing by.",
    "shutdown"         : "Shutting down. Goodbye.",
    "face_not_found"   : "Unauthorized user detected. Ignoring command.",
    "face_found"       : "Identity confirmed. Welcome back.",
    "single_clap"      : "Single clap detected.",
    "double_clap"      : "Double clap detected. Opening browser.",
    "triple_clap"      : "Triple clap detected. Executing action.",
    "short_whistle"    : "Whistle detected. Toggling music.",
    "long_whistle"     : "Long whistle detected. Maximising window.",
    "opening_amathuba" : "Opening Amathuba.",
    "locking"          : "Locking workstation.",
    "sleeping"         : "Initiating sleep mode.",
    "volume_up"        : "Increasing volume.",
    "volume_down"      : "Decreasing volume.",
    "screenshot"       : "Screenshot captured.",
    "not_understood"   : "I did not understand that. Please try again.",
    "cooldown"         : "System cooling down. Please wait.",
    "armed"            : "Jarvis armed. Listening for commands.",
    "disarmed"         : "Jarvis disarmed.",
    "gesture_up"       : "Volume increased.",
    "gesture_down"     : "Volume decreased.",
    "gesture_peace"    : "Screenshot taken.",
    "gesture_palm"     : "Playback toggled.",
}

# ─────────────────────────────────────────────────────────────────────────────
async def _generate_to(text, filepath):
    """Generate speech and save to specified file."""
    communicate = edge_tts.Communicate(text, VOICE, rate=RATE, pitch=PITCH)
    await communicate.save(filepath)
    
def speak(key):
    """Speak a Jarvis response by key name."""
    text = RESPONSES.get(key, key)
    print(f"🤖 Jarvis: '{text}'")

    # ── Unique temp file per call prevents permission conflicts ───────────────
    temp_file = f"assets/jarvis_temp_{uuid.uuid4().hex[:8]}.mp3"

    try:
        asyncio.run(_generate_to(text, temp_file))

        pygame.mixer.music.load(temp_file)
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            time.sleep(0.05)

        pygame.mixer.music.unload()
        time.sleep(0.1)

    except Exception as e:
        print(f"⚠️  Voice error: {e}")

    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)

def cleanup():
    """Call this when shutting down."""
    pygame.mixer.quit()
    if os.path.exists(TEMP_FILE):
        os.remove(TEMP_FILE)