# J.A.R.V.I.S. Automation

J.A.R.V.I.S. Automation is a Windows-based voice and audio control assistant that combines wake-word detection, voice authentication, face presence checks, clap/snap detection, and whistle detection to trigger local desktop actions.

The system is designed to stay in the background, wait for "Hey Jarvis", verify the user, and then execute commands such as opening the browser, opening Amathuba, locking the laptop, changing volume, taking screenshots, or toggling media playback.

## Features

- Wake-word detection with `Hey Jarvis`
- Voice authentication using a saved voiceprint
- Background face monitoring to switch between desk and proximity modes
- Clap/snap detection for quick hands-free actions
- Whistle detection for media and window controls
- Text-to-speech responses for status and feedback
- Optional local roster-cleaning utility

## Requirements

- Windows
- Python 3.10 or newer
- Microphone access
- Webcam access for face monitoring
- A working audio output device
- Microsoft Edge installed at the path used in `modules/actions.py`, or update that path to match your machine

## Installation

1. Clone the repository.
2. Create and activate a virtual environment.
3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Setup

### 1. Configure the app

The main runtime settings live in [config.json](config.json).

Useful values include:

- `cooldown_seconds`: delay between accepted actions
- `jarvis_responses`: spoken phrases returned by the assistant
- `face_check_enabled`: whether face monitoring is enabled

### 2. Record your voiceprint

The assistant uses [assets/voiceprint.npy](assets/voiceprint.npy) for speaker verification. This file is treated as local-only data.

To generate a new voiceprint, run:

```bash
python train_voice.py
```

Then verify it with the voice tests or by running the main app.

### 3. Review app paths

The browser launch path is hardcoded in [modules/actions.py](modules/actions.py). Update it if Microsoft Edge is installed elsewhere on your PC.

The screenshot action saves files to the Desktop path used in the code, which currently assumes a OneDrive-based University of Cape Town desktop folder. Adjust that path if needed.

## Running the Assistant

Start the full assistant with:

```bash
python main.py
```

What happens at startup:

1. The face monitor starts in the background.
2. The wake-word detector listens for "Hey Jarvis".
3. Clap and whistle detectors start in parallel.
4. After the wake word is heard, the assistant listens for a voice command and verifies the speaker.

Press `Ctrl+C` to shut the system down cleanly.

## Supported Commands

### Voice commands

Say "Hey Jarvis" first, then one of the supported phrases:

- `lock` or `jarvis lock`
- `sleep` or `jarvis sleep`
- `open amathuba` or `jarvis open amathuba`
- `open browser` or `jarvis open browser`
- `volume up` or `jarvis volume up`
- `volume down` or `jarvis volume down`
- `screenshot` or `jarvis screenshot`
- `shutdown` or `jarvis shutdown`
- `silent mode` or `jarvis silent mode`
- `vocal mode` or `jarvis vocal mode`
- `stop`, `jarvis stop`, or `deactivate`

### Clap and snap triggers

- 1 clap/snap: open Amathuba
- 2 claps/snaps: open the browser
- 3 claps/snaps: take a screenshot

### Whistle triggers

- Short whistle: play/pause media
- Long whistle: maximise the active window

## Modes

The face monitor decides whether the system is in desk mode or proximity mode.

- Desk mode: full command set is available
- Proximity mode: only a limited set of safer voice commands is allowed

## Tests

The repository includes interactive test scripts for the major subsystems:

- `python test_voice.py`
- `python test_face.py`
- `python test_wake_word.py`
- `python test_clap.py`
- `python test_whistle.py`
- `python test_actions.py`

These scripts are useful for confirming your audio devices, camera, and action mappings before relying on the full assistant.

## Utility Script

`process_roster.py` is a small local utility for cleaning a raw roster export into a simplified surname/first-name format.

Example:

```bash
python process_roster.py input_roster.txt -o cleaned_student_roster.txt
```

If no input file is provided, it looks for `student_roster_raw.txt` in the current folder.

## Project Structure

```text
main.py                 # Main assistant runtime
config.json             # Runtime configuration and spoken responses
process_roster.py       # Optional roster-cleaning utility
train_voice.py          # Voiceprint training script
test_*.py               # Interactive subsystem tests
assets/
  voiceprint.npy        # Saved voiceprint used for authentication
modules/
  actions.py            # Desktop actions triggered by commands
  clap_detector.py      # Clap/snap background detector
  face_check.py         # Background face presence monitor
  gesture_detector.py   # Gesture-based trigger support
  voice_auth.py         # Voice verification logic
  voice.py              # Text-to-speech responses
  wake_word.py          # Hey Jarvis wake-word detector
  whistle_detector.py   # Whistle background detector
```

## Notes

- `assets/voiceprint.npy` and any roster exports should be treated as local-only data.
- Generated audio files and temporary artifacts are cleaned up by the code, but should still be excluded from version control.
- Some actions depend on OS-level behavior such as the Windows lock screen, media keys, and screenshot saving.

## License

Add your preferred license before publishing to GitHub if this project is meant to be shared publicly.