import os
import re
import subprocess
import time

# ─────────────────────────────────────────────────────────────────────────────
# SPOKEN TASK ROUTER
# After a double clap, whatever you say is routed by its first words:
#   "note ..."  → appended to a markdown notes file (no AI, instant)
#   "idea ..."  → dropped into the Autobuilder inbox to be planned and built
#   anything else → opens Claude Code in a new window with the task typed in
# ─────────────────────────────────────────────────────────────────────────────

NOTE_PREFIXES = ("take a note", "make a note", "note that", "note")
IDEA_PREFIXES = ("new idea", "idea")

CLAUDE_PREAMBLE = (
    "This task was spoken to my Jarvis assistant and transcribed by speech "
    "recognition, so words may be misheard. If anything is unclear or risky, "
    "ask me before acting.\n\nTask: "
)

# ─────────────────────────────────────────────────────────────────────────────
def parse_task(text):
    """
    Split spoken text into (kind, body).
    kind is "note", "idea" or "claude".
    """
    text  = text.strip()
    lower = text.lower()
    for kind, prefixes in (("note", NOTE_PREFIXES), ("idea", IDEA_PREFIXES)):
        for prefix in prefixes:
            if re.match(rf"{prefix}\b", lower):
                return kind, text[len(prefix):].lstrip(" :,.-")
    return "claude", text

# ─────────────────────────────────────────────────────────────────────────────
def idea_filename(body):
    """Autobuilder uses the filename as the project name: first 4 words, slugged."""
    words = re.findall(r"[a-z0-9]+", body.lower())[:4]
    return "-".join(words) or "idea"

# ─────────────────────────────────────────────────────────────────────────────
def save_note(body, notes_file):
    os.makedirs(os.path.dirname(notes_file), exist_ok=True)
    with open(notes_file, "a", encoding="utf-8") as f:
        f.write(f"- **{time.strftime('%Y-%m-%d %H:%M')}** {body}\n")
    print(f"✅ Note saved → {notes_file}")

# ─────────────────────────────────────────────────────────────────────────────
def save_idea(body, inbox_dir):
    name = idea_filename(body)
    path = os.path.join(inbox_dir, f"{name}.md")
    n = 2
    while os.path.exists(path):  # never overwrite an earlier idea
        path = os.path.join(inbox_dir, f"{name}-{n}.md")
        n += 1
    with open(path, "w", encoding="utf-8") as f:
        f.write(body + "\n")
    print(f"✅ Idea sent to Autobuilder → {path}")

# ─────────────────────────────────────────────────────────────────────────────
def open_claude(task, claude_path, work_dir):
    """
    Open an interactive Claude Code window with the task pre-filled.
    Args go as a list (never a shell string) so spoken text can't inject commands.
    You stay in the loop: Claude asks before anything risky.
    """
    args = [claude_path] + ([CLAUDE_PREAMBLE + task] if task else [])
    subprocess.Popen(args, cwd=work_dir, creationflags=subprocess.CREATE_NEW_CONSOLE)
    print(f"✅ Claude Code opened in {work_dir}")

# ─────────────────────────────────────────────────────────────────────────────
def route_task(text, config):
    """Route a spoken task. Returns the kind so the caller can speak a reply."""
    kind, body = parse_task(text)
    paths = config["claude"]
    try:
        if kind == "note":
            save_note(body, os.path.expanduser(paths["notes_file"]))
        elif kind == "idea":
            save_idea(body, os.path.expanduser(paths["autobuilder_inbox"]))
        else:
            open_claude(body, os.path.expanduser(paths["claude_path"]),
                        os.path.expanduser(paths["default_dir"]))
    except Exception as e:
        print(f"❌ route_task failed: {e}")
        return "task_failed"
    return f"task_{kind}"
