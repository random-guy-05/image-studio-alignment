# ImageStudio Alignment

> Drag every blue outline circle to its correct data dot — automatically.

<br>

```
image-studio run
```

**One command.** Detects positions, pairs outlines, drags them into place, verifies, and repairs.

---

<br>

## Installation

```bash
npm install -g github:random-guy-05/image-studio-alignment
image-studio init
```

**Requires:** Node.js + Python 3.11–3.13

**macOS:** Enable Accessibility for your terminal when prompted.

**Windows:** Same commands from PowerShell.

---

<br>

## Setup (do this once)

1. Open your file in ImageStudio — full grid visible
2. **Hide** the blue outline circles
3. Take a **full-screen screenshot**
4. Save it as `screenshots/dots.png`
5. **Show** the blue outlines again

---

<br>

## Workflow

```
                    ┌─────────┐
 screenshots ───────► detect  │
 dots.png           └────┬────┘
                         │ 240 target positions
                    ┌────▼────┐
                    │ prepare │  full-screen capture
                    └────┬────┘
                         │ 240 blue→target pairs
                    ┌────▼────┐
                    │  align  │  drag every blue
                    └────┬────┘
                         │
                    ┌────▼────┐
                    │ verify  │  read-only check
                    └────┬────┘
                         │
                    ┌────▼────┐
                    │complete │  repair misalignments
                    └─────────┘
```

**Run it all:**

```bash
image-studio run
```

You'll answer three prompts:
- Row/column count (default 10×24)
- Proceed after reviewing the overlay? (y/n)
- Pixel tolerance for final check (default 5)

---

<br>

## Commands

| Command | What it does |
|---------|-------------|
| `image-studio run` | Full workflow: detect → prepare → align → verify → complete |
| `image-studio detect` | Detect blot positions from screenshot |
| `image-studio prepare` | Scan for blue outlines and pair to targets |
| `image-studio prepare --resume` | Same, works after a partial run |
| `image-studio align` | Drag blues to targets |
| `image-studio verify` | Read-only alignment report |
| `image-studio complete` | Repair anything misaligned |
| `image-studio clean` | Remove generated files |

---

<br>

## Resume After Interruption

```bash
image-studio prepare --resume
image-studio align
```

Already-aligned outlines are automatically skipped.

---

<br>

## Output Files

| File | What's in it |
|------|-------------|
| `screenshots/detected_overlay.png` | Preview: green circles = predicted, red+marker = discovered |
| `predicted_positions.json` | All 240 definitive target coordinates |
| `targets.json` | Current blue-outline-to-target pairs |
| `verification.json` | Alignment report: aligned / misaligned / missing / overlapping |

---

<br>

## Tips

- **Never** include blue outlines in `dots.png`. They must be hidden during the screenshot.
- Press **Ctrl+C** to stop at any time. Use resume commands to continue.
- If macOS asks for Input Monitoring, allow it — pyautogui needs it to move the mouse.
- The overlay at `screenshots/detected_overlay.png` updates after every `detect` — review before aligning.
- Python 3.14 is not yet supported. Use 3.11, 3.12, or 3.13.