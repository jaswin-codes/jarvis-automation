import subprocess
import os
import time
import pyautogui
from modules.voice import speak

# ── Safety setting ────────────────────────────────────────────────────────────
# Moving mouse to top-left corner will abort pyautogui actions
pyautogui.FAILSAFE = True

# ─────────────────────────────────────────────────────────────────────────────
# APP PATHS — update these to match your actual install locations
# ─────────────────────────────────────────────────────────────────────────────
APPS = {
    "amathuba"     : r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "browser"      : r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "amathuba_url" : "https://amathuba.uct.ac.za",
}

# ─────────────────────────────────────────────────────────────────────────────
# CORE ACTIONS
# Each function speaks a response then executes the action.
# All actions are wrapped in try/except so one failure
# doesn't crash the whole system.
# ─────────────────────────────────────────────────────────────────────────────

def open_amathuba():
    """Open Amathuba in Chrome."""
    try:
        speak("opening_amathuba")
        subprocess.Popen([
            APPS["browser"],
            APPS["amathuba_url"]
        ])
        print("✅ Action: Opened Amathuba")
    except Exception as e:
        print(f"❌ open_amathuba failed: {e}")

# ─────────────────────────────────────────────────────────────────────────────
def open_browser():
    """Open Microsoft Edge browser."""
    try:
        speak("double_clap")
        subprocess.Popen([APPS["browser"]])
        print("✅ Action: Opened Edge browser")
    except Exception as e:
        print(f"❌ open_browser failed: {e}")
# ─────────────────────────────────────────────────────────────────────────────
def lock_laptop():
    """Lock the workstation."""
    try:
        speak("locking")
        time.sleep(1.5)  # let Jarvis finish speaking before locking
        subprocess.run([
            "rundll32.exe",
            "user32.dll,LockWorkStation"
        ])
        print("✅ Action: Locked workstation")
    except Exception as e:
        print(f"❌ lock_laptop failed: {e}")

# ─────────────────────────────────────────────────────────────────────────────
def sleep_laptop():
    """Put laptop to sleep."""
    try:
        speak("sleeping")
        time.sleep(1.5)
        subprocess.run([
            "rundll32.exe",
            "powrprof.dll,SetSuspendState",
            "0,1,0"
        ])
        print("✅ Action: Sleep initiated")
    except Exception as e:
        print(f"❌ sleep_laptop failed: {e}")

# ─────────────────────────────────────────────────────────────────────────────
def volume_up():
    """Increase system volume by ~10%."""
    try:
        speak("volume_up")
        for _ in range(5):
            pyautogui.press("volumeup")
        print("✅ Action: Volume up")
    except Exception as e:
        print(f"❌ volume_up failed: {e}")

# ─────────────────────────────────────────────────────────────────────────────
def volume_down():
    """Decrease system volume by ~10%."""
    try:
        speak("volume_down")
        for _ in range(5):
            pyautogui.press("volumedown")
        print("✅ Action: Volume down")
    except Exception as e:
        print(f"❌ volume_down failed: {e}")

# ─────────────────────────────────────────────────────────────────────────────
def mute_toggle():
    """Toggle mute."""
    try:
        pyautogui.press("volumemute")
        print("✅ Action: Mute toggled")
    except Exception as e:
        print(f"❌ mute_toggle failed: {e}")

# ─────────────────────────────────────────────────────────────────────────────
def take_screenshot():
    """Take a screenshot and save to Desktop."""
    try:
        speak("screenshot")
        time.sleep(0.5)
        timestamp  = time.strftime("%Y%m%d_%H%M%S")
        desktop = os.path.join(os.path.expanduser("~"), 
                    "OneDrive - University of Cape Town", "Desktop")
        filepath   = os.path.join(desktop, f"jarvis_screenshot_{timestamp}.png")
        screenshot = pyautogui.screenshot()
        screenshot.save(filepath)
        print(f"✅ Action: Screenshot saved → {filepath}")
    except Exception as e:
        print(f"❌ take_screenshot failed: {e}")

# ─────────────────────────────────────────────────────────────────────────────
def maximize_window():
    """Maximise the current active window."""
    try:
        speak("long_whistle")
        pyautogui.hotkey("win", "up")
        print("✅ Action: Window maximised")
    except Exception as e:
        print(f"❌ maximize_window failed: {e}")

# ─────────────────────────────────────────────────────────────────────────────
def play_pause_media():
    """Toggle play/pause for media."""
    try:
        speak("short_whistle")
        pyautogui.press("playpause")
        print("✅ Action: Play/pause toggled")
    except Exception as e:
        print(f"❌ play_pause_media failed: {e}")

# ─────────────────────────────────────────────────────────────────────────────
def shutdown_laptop():
    """Shutdown the laptop."""
    try:
        speak("shutdown")
        time.sleep(2)  # let Jarvis finish speaking
        subprocess.run(["shutdown", "/s", "/t", "10"])
        print("✅ Action: Shutdown initiated in 10 seconds")
        print("   Run 'shutdown /a' to abort!")
    except Exception as e:
        print(f"❌ shutdown_laptop failed: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# ACTION MAP — maps string keys to functions
# This is what main.py and all modules use to trigger actions
# ─────────────────────────────────────────────────────────────────────────────
ACTION_MAP = {
    # Clap/snap triggers
    "single_clap"  : open_amathuba,
    "double_clap"  : open_browser,
    "triple_clap"  : take_screenshot,

    # Whistle triggers
    "short_whistle": play_pause_media,
    "long_whistle" : maximize_window,

    # Voice commands
    "opening_amathuba" : open_amathuba,
    "locking"          : lock_laptop,
    "sleeping"         : sleep_laptop,
    "volume_up"        : volume_up,
    "volume_down"      : volume_down,
    "screenshot"       : take_screenshot,
    "shutdown"         : shutdown_laptop,
    "double_clap"      : open_browser,

    # Gesture triggers (Stage 11)
    "gesture_up"   : volume_up,
    "gesture_down" : volume_down,
    "gesture_peace": take_screenshot,
    "gesture_palm" : play_pause_media,
}

# ─────────────────────────────────────────────────────────────────────────────
def execute(action_key):
    """
    Execute an action by key name.
    Example: execute("lock") → calls lock_laptop()
    """
    action = ACTION_MAP.get(action_key)
    if action:
        print(f"🎯 Executing action: '{action_key}'")
        action()
    else:
        print(f"⚠️  Unknown action key: '{action_key}'")
        speak("not_understood")