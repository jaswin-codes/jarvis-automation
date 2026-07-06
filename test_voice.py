from modules.voice import speak, cleanup
import time

print("=== JARVIS - Voice Module Test ===\n")

# Test a few key lines
test_keys = [
    "startup",
    "systems_online",
    "armed",
    "face_not_found",
    "opening_amathuba",
    "locking",
    "shutdown",
]

for key in test_keys:
    speak(key)
    time.sleep(0.3)

cleanup()
print("\n✅ Voice module working correctly.")