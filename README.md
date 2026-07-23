# ImageStudio Alignment

Automatically moves ImageStudio's blue outline circles onto their correct data dots.

**One command does everything:**

```bash
image-studio run
```

---

## What It Does

| Step | Description |
|------|-------------|
| 1. Detect | Learns all 240 blot positions from a clean screenshot |
| 2. Prepare | Captures the screen, pairs each blue outline to its target |
| 3. Align | Drags every blue circle to its correct data dot |
| 4. Verify | Checks every position and reports misalignments |
| 5. Complete | Fixes any remaining misalignments (asks for tolerance) |

---

## Install (30 seconds)

**Prerequisites**: Node.js + Python 3

```bash
npm install -g github:random-guy-05/image-studio-alignment
image-studio init
```

This creates a private Python environment. No clone, no manual setup.

**macOS**: grant Accessibility permission when prompted (System Settings → Privacy & Security → Accessibility).

**Windows**: same commands from PowerShell. Python 3.11–3.13 required.

---

## One-Time Setup

1. Open ImageStudio — full grid must be visible
2. **Hide** blue outline circles
3. Take a **full-screen screenshot**
4. Save to `screenshots/dots.png`
5. **Show** blue outlines again

---

## Run Everything

```bash
image-studio run
```

You'll be asked:
- **Row/column count** — default is 10×24, press Enter to accept
- **Proceed?** — type `y` after reviewing the overlay at `screenshots/detected_overlay.png`
- **Tolerance** — how strict the final check should be in pixels (default 5)

---

## Individual Commands

| Command | Purpose |
|---------|---------|
| `image-studio detect` | Detect blot positions from the clean screenshot |
| `image-studio prepare` | Pair visible blue outlines to targets |
| `image-studio prepare --resume` | Same but works after a partial run |
| `image-studio align` | Drag blues to targets |
| `image-studio verify` | Read-only check — writes `verification.json` |
| `image-studio complete` | Repair remaining misalignments |
| `image-studio clean` | Delete generated files (keeps `dots.png`) |

---

## Resume After Interruption

```bash
image-studio prepare --resume
image-studio align
```

Already-aligned outlines are skipped.

---

## Generated Files

| File | Purpose |
|------|---------|
| `screenshots/detected_overlay.png` | Preview: green=predicted, red=discovered |
| `predicted_positions.json` | All 240 target coordinates |
| `targets.json` | Blue-to-target pairs |
| `verification.json` | Alignment report |

---

## Recovery

Press **Ctrl+C** anytime. Reopen/reset the ImageStudio file, show blue outlines, then:

```bash
image-studio prepare --resume
image-studio align
```

**Important**: never include blue outlines in `dots.png` — they must be hidden during capture.
