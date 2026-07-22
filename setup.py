#!/usr/bin/env python3
"""
STEP 1: Setup — detect data dots from the clean screenshot, then detect
blue circles from the current ImageStudio view, pair them, and save.

Workflow:
  1. In ImageStudio: hide the blue-outline circles
  2. Take a screenshot, save to /tmp/dots.png
  3. In ImageStudio: show the blue-outline circles again
  4. Run: python3 setup.py
"""
import json, math, subprocess, time, sys
import cv2
import numpy as np
from scipy.optimize import linear_sum_assignment

DOTS_IMAGE = "/tmp/dots.png"

def get_main_window():
    raw = subprocess.check_output(["osascript", "-e",
        'tell application "System Events" to tell process "ImageStudio" to get position of every window & size of every window'
    ]).decode().strip()
    # Parse: format is like "x1, y1, x2, y2, w1, h1, w2, h2"
    # but may have "missing value" for empty fields
    parts = []
    for p in raw.replace("{","").replace("}","").split(","):
        p = p.strip()
        if p == "missing value" or p == "":
            parts.append(0)
        else:
            try:
                parts.append(int(p))
            except ValueError:
                parts.append(0)
    nums = parts
    n = len(nums) // 4
    windows = []
    for i in range(n):
        x, y = nums[i*2], nums[i*2+1]
        w, h = nums[n*2 + i*2], nums[n*2 + i*2 + 1]
        if w == 0 or h == 0:
            continue
        windows.append((x, y, w, h, w*h))
    windows.sort(key=lambda w: -w[4])
    return windows[0][:4]

# Load screenshot
print(f"Loading: {DOTS_IMAGE}")
img = cv2.imread(DOTS_IMAGE)
if img is None:
    print(f"ERROR: {DOTS_IMAGE} not found", flush=True); sys.exit(1)
H, W = img.shape[:2]
print(f"  Screenshot: {W}x{H}")

# Find the THIN BLUE RECTANGLE in the screenshot
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
blue_mask = cv2.inRange(hsv, np.array((100, 120, 100)), np.array((130, 255, 255)))
def longest_runs(mask, axis):
    out = np.zeros(mask.shape[axis], dtype=int)
    for i in range(mask.shape[axis]):
        line = (mask.take(i, axis=axis) > 0)
        if not line.any(): continue
        padded = np.concatenate(([False], line, [False]))
        diffs = np.diff(padded.astype(int))
        starts = np.where(diffs == 1)[0]; ends = np.where(diffs == -1)[0]
        if len(starts): out[i] = (ends - starts).max()
    return out

lh = longest_runs(blue_mask, 0)
lv = longest_runs(blue_mask, 1)
# CORNER-BASED RECTANGLE DETECTION
# The rectangle's 4 corners are where long horizontal runs intersect
# with long vertical runs. The toolbar and data borders only have
# horizontal runs (no vertical), so they won't produce corners.
# This reliably isolates the rectangle from other blue features.

# Build mask of pixels in long horizontal runs (>200px)
h_mask = np.zeros_like(blue_mask)
for y in range(H):
    row = blue_mask[y] > 0
    if not row.any(): continue
    padded = np.concatenate(([False], row, [False]))
    diffs = np.diff(padded.astype(int))
    starts = np.where(diffs == 1)[0]
    ends = np.where(diffs == -1)[0]
    for s, e in zip(starts, ends):
        if e - s > 200:
            h_mask[y, s:e] = 255

# Build mask of pixels in long vertical runs (>100px)
v_mask = np.zeros_like(blue_mask)
for x in range(W):
    col = blue_mask[:, x] > 0
    if not col.any(): continue
    padded = np.concatenate(([False], col, [False]))
    diffs = np.diff(padded.astype(int))
    starts = np.where(diffs == 1)[0]
    ends = np.where(diffs == -1)[0]
    for s, e in zip(starts, ends):
        if e - s > 100:
            v_mask[s:e, x] = 255

# Corners = intersection of both masks
corners = cv2.bitwise_and(h_mask, v_mask)
corner_count = int((corners > 0).sum())
print(f"  Corner pixels (h-run ∩ v-run): {corner_count}")

if corner_count == 0:
    print(f"ERROR: no rectangle corners found", flush=True)
    sys.exit(1)

# Cluster corner pixels and EXCLUDE clusters near the image edges
# (screen borders, window edges produce false corners)
EDGE_EXCLUDE = 100
ys, xs = np.where(corners > 0)
from collections import defaultdict
clusters = defaultdict(list)
for y, x in zip(ys, xs):
    if x < EDGE_EXCLUDE or x > W - EDGE_EXCLUDE: continue
    if y < EDGE_EXCLUDE or y > H - EDGE_EXCLUDE: continue
    clusters[(y//20, x//20)].append((y, x))

if len(clusters) < 4:
    print(f"ERROR: only {len(clusters)} corner clusters (need 4)", flush=True)
    sys.exit(1)

# Get cluster centers
centers = []
for key, pts in clusters.items():
    cy = sum(p[0] for p in pts) / len(pts)
    cx = sum(p[1] for p in pts) / len(pts)
    centers.append((cx, cy))

# The rectangle: bounding box of all cluster centers
rect_left = int(min(c[0] for c in centers))
rect_right = int(max(c[0] for c in centers))
rect_top = int(min(c[1] for c in centers))
rect_bot = int(max(c[1] for c in centers))
print(f"  Blue rectangle: x=[{rect_left},{rect_right}]  y=[{rect_top},{rect_bot}]  ({rect_right-rect_left}x{rect_bot-rect_top})")

# Detect data dots INSIDE the blue rectangle using HoughCircles
# V < 215 catches black + all greys + REALLY light greys (V 200-215).
# V < 220 catches too much noise and actually finds FEWER dots.
data_mask = cv2.inRange(hsv, np.array((0, 0, 0)), np.array((180, 50, 215)))
# Zero out everything outside the rectangle
data_mask[:rect_top, :] = 0
data_mask[rect_bot:, :] = 0
data_mask[:, :rect_left] = 0
data_mask[:, rect_right:] = 0
blurred = cv2.GaussianBlur(data_mask, (5, 5), 1)
circles = cv2.HoughCircles(blurred, cv2.HOUGH_GRADIENT, dp=1, minDist=15,
                            param1=80, param2=12, minRadius=3, maxRadius=15)
data_dots_raw = [] if circles is None else [(int(x), int(y)) for x, y, r in circles[0]]
# STRICT POST-FILTER: only keep circles whose CENTER is strictly inside the
# rectangle. Hough can return circles just outside the masked area.
# We use < not <= so circles exactly on the edge are also excluded.
data_dots = [(x, y) for x, y in data_dots_raw
             if rect_left < x < rect_right and rect_top < y < rect_bot]
removed = len(data_dots_raw) - len(data_dots)
print(f"  Data dots: {len(data_dots_raw)} raw  {len(data_dots)} inside rectangle  ({removed} removed)")

# === ALERT: tell the user the count, give them 30s to adjust blue circles ===
n_dots = len(data_dots)
print(f"\n  Data dots inside rectangle: {n_dots}")
print(f"\a", end="", flush=True)  # terminal bell

# Show a MODAL DIALOG with sound (always visible, can't be missed)
# Auto-dismisses after 30 seconds if user doesn't click OK
dialog_script = f'''
display dialog "Found {n_dots} data dots in the screenshot.

Adjust the number of BLUE CIRCLES in ImageStudio to match ({n_dots}).

Click OK when ready (or wait 30 seconds)." with title "ImageStudio Align" with icon caution giving up after 30
'''
try:
    subprocess.run(["osascript", "-e", dialog_script], check=False, timeout=35)
except subprocess.TimeoutExpired:
    pass
print(f"\n  ========================================")
print(f"  ALERT: Found {n_dots} data dots.")
print(f"  Adjust blue circles in ImageStudio to match.")
print(f"  Now continuing with detection of blue circles…")
print(f"  ========================================")

# Get current ImageStudio view for blue circles
wx, wy, ww, wh = get_main_window()
# The screenshot is a FULL-SCREEN capture at 1x scale.
# Screenshot pixels = screen points directly.
# The window capture is also at 1x (verified: 1820px for 1820pt window).
# So:
#   data dots: screen_x = screenshot_x, screen_y = screenshot_y (NO conversion)
#   blue circles: screen_x = wx + capture_x, screen_y = wy + capture_y (window offset only)
print(f"\n  Current window: ({wx},{wy}) {ww}x{wh}")
print(f"  Screenshot: {W}x{H} (full screen, 1x scale → screenshot pixels = screen points)")

# Capture current view
for _ in range(3):
    subprocess.run(["osascript", "-e", 'tell application "ImageStudio" to activate'], check=True)
    time.sleep(0.3)
subprocess.run(["screencapture", "-R", f"{wx},{wy},{ww},{wh}", "/tmp/blues.png"], check=True)
img2 = cv2.imread("/tmp/blues.png")
hsv2 = cv2.cvtColor(img2, cv2.COLOR_BGR2HSV)
blue_mask2 = cv2.inRange(hsv2, np.array((100, 120, 100)), np.array((130, 255, 255)))

# The rectangle in SCREEN coordinates = screenshot coordinates (1x)
cur_left = rect_left
cur_right = rect_right
cur_top = rect_top
cur_bot = rect_bot
print(f"  Rectangle (screen coords): x=[{cur_left},{cur_right}]  y=[{cur_top},{cur_bot}]")

# Detect blue circles in current view (window capture at 1x)
r_min = max(4, int(6)); r_max = max(10, int(18))
bb = cv2.GaussianBlur(blue_mask2, (5, 5), 1)
b_circles = cv2.HoughCircles(bb, cv2.HOUGH_GRADIENT, dp=1, minDist=15, param1=80, param2=30,
                              minRadius=r_min, maxRadius=r_max)
blue_circles_all = [] if b_circles is None else [(int(x), int(y), int(r)) for x, y, r in b_circles[0]]
# Convert blue circles to SCREEN coordinates: screen = window_offset + capture_pixel
blue_circles_screen = [(wx + b[0], wy + b[1], b[2]) for b in blue_circles_all]
# FILTER: only keep blue circles INSIDE the rectangle (in screen coords)
blue_circles = [b for b in blue_circles_screen
                if cur_left < b[0] < cur_right and cur_top < b[1] < cur_bot]
print(f"  Blue circles: {len(blue_circles_all)} total, {len(blue_circles)} inside rectangle")

# Pair each blue with its nearest data dot
# Data dots are in SCREEN coordinates (screenshot = full screen at 1x)
# Blue circles are in SCREEN coordinates (window_offset + capture_pixel)
n = min(len(blue_circles), len(data_dots))
cost = np.full((len(blue_circles), len(data_dots)), 1e6)
for i, (bx, by, _) in enumerate(blue_circles):
    for j, (dx, dy) in enumerate(data_dots):
        cost[i, j] = math.hypot(bx - dx, by - dy)
row, col = linear_sum_assignment(cost)

pairs = []
for r, c in zip(row, col):
    if cost[r, c] < 1e5:
        bx, by, _ = blue_circles[r]
        dx, dy = data_dots[c]
        # Both are already in screen coordinates — no conversion needed
        pairs.append({
            "dot":  [bx, by],   # blue circle center (screen coords)
            "spot": [dx, dy],   # data dot center (screen coords)
        })

print(f"\n  ========================================")
print(f"  Data dots found:    {len(data_dots)}")
print(f"  Blue circles found: {len(blue_circles)}")
print(f"  Pairs:              {len(pairs)}")
print(f"  ========================================")
if len(blue_circles) != len(data_dots):
    print(f"\n  WARNING: counts don't match. {len(blue_circles) - len(data_dots)} extra blues will be skipped.")
    print(f"  (If you wanted to match the counts, hide blues and re-run setup.py.)")

# Save — rectangle is in SCREEN coordinates (same as screenshot)
out = {
    "bounds": [wx, wy, ww, wh],
    "rectangle": [rect_left, rect_top, rect_right, rect_bot],
    "pairs": pairs,
}
with open("/Users/admin/opencode-imagestudio/targets.json", "w") as f:
    json.dump(out, f, indent=2)
print(f"\nSaved targets.json")
print(f"  Click zone (screen coords): {out['rectangle']}")
