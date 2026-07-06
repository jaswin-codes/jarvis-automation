from modules.actions import execute
import time

print("=== JARVIS - System Actions Test ===\n")
print("We will test each action one by one.")
print("⚠️  WARNING: Some actions will actually run!")
print("   shutdown test is SKIPPED for safety.\n")

# ── Test menu ─────────────────────────────────────────────────────────────────
actions_to_test = [
    ("volume_up",      "Volume should increase"),
    ("volume_down",    "Volume should decrease"),
    ("screenshot",     "Screenshot saved to Desktop"),
    ("short_whistle",  "Media should play/pause"),
    ("long_whistle",   "Window should maximise"),
    ("double_clap",    "Browser should open"),
    ("single_clap",    "Amathuba should open in browser"),
    ("triple_clap",    "Screenshot taken"),
    ("locking",        "💻 LAPTOP WILL LOCK — log back in after!"),
]

for i, (action, description) in enumerate(actions_to_test, 1):
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"Test {i}/{len(actions_to_test)}: {action}")
    print(f"   Expected: {description}")
    choice = input("   Run this test? (y/n/q to quit): ").strip().lower()

    if choice == 'q':
        print("\n🛑 Stopped.")
        break
    elif choice == 'y':
        execute(action)
        print(f"   ✅ Done")
        time.sleep(2)
    else:
        print("   ⏭️  Skipped")

print("\n✅ Actions test complete.")