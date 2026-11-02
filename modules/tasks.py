import os
import re
import subprocess
import time

# ─────────────────────────────────────────────────────────────────────────────
# SPOKEN TASK ROUTER
# After a double clap, whatever you say is routed by its first words:
#   "note ..."  → appended to a markdown notes file (no AI, instant)
#   "idea ..."  → dropped into the Autobuilder inbox to be planned and built
#   "search ...", "who/what/when ..." → Claude looks it up in Chrome and
#                   Jarvis speaks the answer
#   anything else → opens Claude Code in a new window with the task typed in
# ─────────────────────────────────────────────────────────────────────────────

NOTE_PREFIXES = ("take a note", "make a note", "note that", "note")
IDEA_PREFIXES = ("new idea", "idea")
WEB_PREFIXES  = ("open google and", "open google", "google", "search for", "search",
                 "look up", "find out", "check", "who", "what", "when", "where",
                 "which", "how many", "how much")
# The answer comes back as stdout and is spoken, so keep it short and plain
WEB_PROMPT = (
    "You are Jarvis, my voice assistant. This request was spoken and transcribed "
    "by speech recognition, so words may be misheard. Answer it using the Chrome "
    "browser tools in a new tab so I can watch. Only read pages: never sign in, "
    "submit forms, buy, post or download anything. Reply with only the answer as "
    "one or two short spoken sentences of at most 25 words total, with no markdown, "
    "lists or links. If there are many results, name the top few and say how many more.\n\nRequest: "
)
WEB_TIMEOUT = 240   # seconds before giving up on a browser lookup

CLAUDE_PREAMBLE = (
    "This task was spoken to my Jarvis assistant and transcribed by speech "
    "recognition, so words may be misheard. If anything is unclear or risky, "
    "ask me before acting.\n\nTask: "
)

# ─────────────────────────────────────────────────────────────────────────────
def parse_task(text):
    """
    Split spoken text into (kind, body).
    kind is "note", "idea", "web" or "claude".
    """
    text  = text.strip()
    lower = text.lower()
    for kind, prefixes in (("note", NOTE_PREFIXES), ("idea", IDEA_PREFIXES)):
        for prefix in prefixes:
            if re.match(rf"{prefix}\b", lower):
                return kind, text[len(prefix):].lstrip(" :,.-")
    # Web lookups keep the whole sentence: "who is playing" reads better than "is playing"
    if any(re.match(rf"{prefix}\b", lower) for prefix in WEB_PREFIXES):
        return "web", text
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
def ask_web(question, claude_path, work_dir, model=None):
    """
    Run Claude headless with Claude in Chrome and return its spoken answer.
    Only the browser tools are allowed; shell and file edits are blocked.
    model picks a faster model than the default (None = Claude's default).
    """
    result = subprocess.run(
        [claude_path, "-p", WEB_PROMPT + question, "--chrome",
         *(["--model", model] if model else []),
         "--allowedTools", "mcp__claude-in-chrome",
         # WebSearch/WebFetch off so it uses the Chrome tab you can watch
         "--disallowedTools", "Bash,Edit,Write,NotebookEdit,WebSearch,WebFetch"],
        cwd=work_dir, capture_output=True, text=True, encoding="utf-8",
        timeout=WEB_TIMEOUT, creationflags=subprocess.CREATE_NO_WINDOW,
    )
    answer = result.stdout.strip()
    if result.returncode != 0 or not answer:
        raise RuntimeError(f"claude exited {result.returncode}: {result.stderr.strip()[:200]}")
    print(f"✅ Web answer: {answer}")
    return answer

# ─────────────────────────────────────────────────────────────────────────────
def route_task(text, config, say=print):
    """
    Route a spoken task. Returns what Jarvis should say next: a voice line key,
    or for web lookups the answer itself. say() is used for "checking now".
    """
    kind, body = parse_task(text)
    paths = config["claude"]
    try:
        if kind == "note":
            save_note(body, os.path.expanduser(paths["notes_file"]))
        elif kind == "idea":
            save_idea(body, os.path.expanduser(paths["autobuilder_inbox"]))
        elif kind == "web":
            say("task_web")
            return ask_web(body, os.path.expanduser(paths["claude_path"]),
                           os.path.expanduser(paths["default_dir"]),
                           paths.get("web_model"))
        else:
            open_claude(body, os.path.expanduser(paths["claude_path"]),
                        os.path.expanduser(paths["default_dir"]))
    except Exception as e:
        print(f"❌ route_task failed: {e}")
        return "task_failed"
    return f"task_{kind}"
