# Run: python test_tasks.py  (no mic, camera or Claude needed)
import os
import tempfile
from modules.tasks import parse_task, idea_filename, save_note, save_idea

assert parse_task("Note: buy resistors") == ("note", "buy resistors")
assert parse_task("take a note the BMS model needs SOC") == ("note", "the BMS model needs SOC")
assert parse_task("notebook pages are messy") == ("claude", "notebook pages are messy")
assert parse_task("New idea, a plant watering robot") == ("idea", "a plant watering robot")
assert parse_task("idealism essay") == ("claude", "idealism essay")
assert parse_task("remind me to email Dr Patil on Monday") == ("claude", "remind me to email Dr Patil on Monday")

assert idea_filename("A plant-watering robot with ESP32") == "a-plant-watering-robot"
assert idea_filename("...") == "idea"

with tempfile.TemporaryDirectory() as d:
    notes = os.path.join(d, "sub", "notes.md")
    save_note("first", notes)
    save_note("second", notes)
    assert open(notes, encoding="utf-8").read().count("\n") == 2

    save_idea("desk robot", d)
    save_idea("desk robot", d)
    assert sorted(f for f in os.listdir(d) if f.endswith(".md")) == ["desk-robot-2.md", "desk-robot.md"]

print("✅ test_tasks passed")
