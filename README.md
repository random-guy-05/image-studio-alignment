# ImageStudio Alignment

Cross-platform automation for moving ImageStudio’s blue outline circles onto a learned 10x24 blot grid.

The project treats the modeled 240 positions as definitive targets. It uses conservative Hough anchors, uneven row/column modeling, row tilt correction, black-blot center correction, verifier-driven repair, and resumable alignment.

## Install

### Recommended: no clone required

Install the global command directly from GitHub:

```bash
npm install -g github:random-guy-05/image-studio-alignment
```

Then create a workspace anywhere:

```bash
mkdir image-studio-workspace
cd image-studio-workspace
image-studio init
```

The npm installer creates the private Python environment automatically. No repository clone is required.

After installation, the complete happy path is:

```bash
image-studio init
image-studio run
```

### macOS, Intel or Apple Silicon

The global npm command works on both Intel and Apple Silicon Macs. If you already cloned the repository instead, `./install.sh` remains available.

If macOS asks for permissions, allow your terminal or Python access under:

`System Settings -> Privacy & Security -> Accessibility`

Allow keyboard monitoring as well if macOS requests it; this enables global ESC cancellation while ImageStudio is focused.

The same Python workflow supports Intel Macs and Apple Silicon Macs; use the native Python installed on that machine.

### Windows

Install Node.js and Python 3, then run from PowerShell anywhere:

```powershell
npm install -g github:random-guy-05/image-studio-alignment
mkdir image-studio-workspace
cd image-studio-workspace
image-studio init
```

If you already cloned the repository, `install.ps1` remains available. Then run the CLI with:

```powershell
python .\image_studio.py --help
python .\image_studio.py detect
```

If the application title is not exactly `ImageStudio`, set it before running:

```powershell
$env:IMAGESTUDIO_WINDOW_TITLE = "Your ImageStudio Window Title"
```

## Daily Workflow

### One command

Once `screenshots/dots.png` is clean and the blue outlines are visible:

```bash
image-studio run
```

This runs detect, prepare, align, and verify in one sequence.

On Windows, use the same command from PowerShell:

```powershell
image-studio run
```

Press `Esc` at any time to abort. The current drag is released safely and the workflow can be resumed with:

```bash
image-studio prepare --resume
image-studio align
```

### 1. Capture the clean blot image

1. Open the ImageStudio file and show the full grid.
2. Hide the blue outline circles.
3. Capture the entire screen, not just the window.
4. Save it as `screenshots/dots.png`.
5. Show the blue outlines again.

The clean screenshot must contain the blot grid without blue outline contamination.

### 2. Learn targets

```bash
./image_studio.py detect
```

This writes `predicted_positions.json` with all 240 definitive blot centers and regenerates the plain center overlay at `screenshots/detected_overlay.png`.

### 3. Prepare center pairs

```bash
./image_studio.py prepare
```

This captures the current full screen, detects blue outline centers, and writes `targets.json`.

For a partially completed run:

```bash
./image_studio.py prepare --resume
```

Resume mode allows fewer visible outlines and is safe for continuation after a timeout or interruption.

### 4. Align

```bash
./image_studio.py align
```

The aligner verifies window bounds, skips centers already within 10 pixels of their targets, and drags only remaining pairs.

### 5. Verify

```bash
./image_studio.py verify
```

The verifier compares current blue centers against all 240 definitive targets and writes `verification.json`.

### 6. Repair anything missing

```bash
./image_studio.py complete
```

This uses `verification.json` logic to create a temporary repair set, aligns only misaligned visible centers, and verifies again.

## Direct Commands

```bash
./image_studio.py --help
./image_studio.py detect
./image_studio.py prepare
./image_studio.py prepare --resume
./image_studio.py align
./image_studio.py verify --tolerance 10
./image_studio.py complete --tolerance 10
```

Equivalent npm shortcuts:

```bash
npm run detect
npm run targets
npm run align
npm run verify
npm run complete
```

Those `npm run` shortcuts are for a cloned developer checkout; global users should use the `image-studio` command directly.

On Windows, replace `./image_studio.py` with `python .\image_studio.py`.

## Important Files

- `image_studio.py`: unified CLI
- `install.sh`: one-command environment setup
- `install.ps1`: Windows PowerShell environment setup
- `platform_utils.py`: Intel Mac, Apple Silicon Mac, and Windows window/capture helpers
- `grid_detect.py`: clean blot detection and 240-position modeling
- `prepare_targets.py`: full-screen blue-center detection and pairing
- `align.py`: guarded center-to-center dragging
- `verify_alignment.py`: read-only alignment verifier
- `complete_alignment.py`: verifier-driven repair pass
- `predicted_positions.json`: definitive modeled centers
- `targets.json`: current blue-to-target pairs
- `verification.json`: latest verification report
- `archive/`: historical experiments and diagnostics

## Recovery

If a run needs to stop, press `Ctrl-C` in the terminal. Reopen/reset the ImageStudio file if necessary, show the blue outlines, and use:

```bash
./image_studio.py prepare --resume
./image_studio.py align
```

Never run alignment against a contaminated `screenshots/dots.png`; blue outlines must be hidden during target detection.
