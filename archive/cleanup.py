"""Clean up the project folder: archive old scripts, keep only the new approach scripts."""
import os, glob, shutil

base = "/Users/admin/opencode-imagestudio"
os.makedirs(f"{base}/archive", exist_ok=True)

# Files to KEEP in the main folder
keep = {
    "align.py",           # the drag script (will be updated)
    "screenshots",        # user's screenshots
    "archive",            # old stuff
    ".venv",              # python venv
    "README.md",          # workflow doc (will create)
    "detect_dots.py",     # NEW: detect data dots from clean screenshot
    "detect_blues.py",    # NEW: detect blue circles from current view
    "cleanup_extras.py",  # NEW: move extras to corner
    "targets.json",       # will be regenerated
}

# Archive everything else
moved = 0
for f in os.listdir(base):
    if f in keep or f.startswith("."):
        continue
    src = os.path.join(base, f)
    if os.path.isfile(src):
        shutil.move(src, os.path.join(base, "archive", f))
        moved += 1

print(f"Archived {moved} files to {base}/archive/")
print(f"Kept: {sorted(keep & set(os.listdir(base)))}")
