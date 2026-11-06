# ImageStudio Alignment

Automates aligning ImageStudio's blue outline circles to their data dots. It detects the dot grid from a screenshot, pairs each outline with a target, drags it into place, then checks and repairs the result.

## Install

Requires Node.js and Python 3.11–3.13 (pyautogui does not support 3.14 yet).

```bash
npm install -g github:random-guy-05/image-studio-alignment
image-studio init
```

The first run creates a Python virtual environment inside the package and installs `requirements.txt`.

On macOS, allow Accessibility (and Input Monitoring, if asked) for your terminal so pyautogui can move the mouse. On Windows, run the same commands from PowerShell.

## One-time setup

1. Open the file in ImageStudio with the full grid visible.
2. Hide the blue outline circles.
3. Take a full-screen screenshot and save it as `screenshots/dots.png`.
4. Show the blue outlines again.

The screenshot must not contain any blue outlines.

## Usage

```bash
image-studio run
```

`run` executes every step in order and asks you three things: the grid size (default 10×24), whether to continue after you review the detection overlay, and the pixel tolerance for the final check (default 5).

| Command | What it does |
|---|---|
| `image-studio run` | Detect, prepare, align, verify, then repair |
| `image-studio detect` | Find the target dot positions in `screenshots/dots.png` |
| `image-studio prepare [--resume]` | Find the blue outlines and pair each with a target |
| `image-studio align` | Drag each outline to its target |
| `image-studio verify` | Report alignment without moving anything |
| `image-studio complete` | Repair only the outlines `verify` flagged |
| `image-studio clean` | Delete generated files (keeps `screenshots/dots.png`) |

Press Ctrl+C to stop at any point. To continue after an interruption, run `image-studio prepare --resume` and then `image-studio align`. Outlines that are already aligned are skipped.

## Generated files

| File | Contents |
|---|---|
| `screenshots/detected_overlay.png` | Detected targets drawn over the screenshot. Check it before aligning. |
| `predicted_positions.json` | All target coordinates |
| `targets.json` | Current outline-to-target pairs |
| `verification.json` | Aligned, misaligned, missing and overlapping outlines |

## Layout

```
bin/image-studio.js   npm entry point; manages the Python environment
src/image_studio.py   command-line interface
src/                  detection, pairing, alignment and verification steps
scripts/              standalone installers (install.sh, install.ps1)
```
