"""Detect ALL blue rings and ALL grey dots in the band above the blue line.
Pair all blues to greys with Hungarian (no 'already aligned' filter).
Drag every single blue to its target."""
import subprocess, json, math, sys
import cv2, numpy as np
from scipy.optimize import linear_sum_assignment

for _ in range(3):
    subprocess.run(["osascript", "-e", 'tell application "ImageStudio" to activate'], check=True)
import time
time.sleep(0.5)

out = subprocess.check_output(["osascript", "-e",
    'tell application "System Events" to tell process "ImageStudio" to get position of front window & size of front window'
]).decode().strip()
nums = [int(x.strip()) for x in out.replace("{","").replace("}","").split(",")]
wx, wy, ww, wh = nums
print(f"Window: ({wx},{wy}) {ww}x{wh}")

subprocess.run(["screencapture", "-R", f"{wx},{wy},{ww},{wh}", "/tmp/v6.png"], check=True)
img = cv2.imread("/tmp/v6.png")
H, W = img.shape[:2]
scale = W / ww
print(f"Image: {W}x{H}  scale={scale:.2f}x")

hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
blue_mask  = cv2.inRange(hsv, np.array((100, 120, 100)), np.array((130, 255, 255)))
# Data dots: V < 180, S < 50 — catches black (V~0) and dark grey, excludes
# anti-aliased blue edges (V~200-215) and blue interiors (V>=220).
data_mask = cv2.inRange(hsv, np.array((0, 0, 0)), np.array((180, 50, 180)))

# Find the blue line (the bottom boundary) — optional, fall back to full image
row_blue = blue_mask.sum(axis=1) / 255
longest_run = np.zeros(H, dtype=int)
for y in range(H):
    row = blue_mask[y] > 0
    if not row.any():
        continue
    padded = np.concatenate(([False], row, [False]))
    diffs = np.diff(padded.astype(int))
    starts = np.where(diffs == 1)[0]
    ends = np.where(diffs == -1)[0]
    runs = ends - starts
    if len(runs):
        longest_run[y] = runs.max()
LINE_MIN_RUN = max(100, int(W * 0.3))
line_rows = np.where(longest_run >= LINE_MIN_RUN)[0]
if len(line_rows) > 0:
    clusters = [[line_rows[0]]]
    for r in line_rows[1:]:
        if r - clusters[-1][-1] <= 3:
            clusters[-1].append(r)
        else:
            clusters.append([r])
    line_bands = [(min(c), max(c)) for c in clusters]
    line_bands.sort(key=lambda b: b[0])
    bot_y_phys = (line_bands[0][0] + line_bands[0][1]) // 2
    print(f"Blue line at row {bot_y_phys}; valid band: 0 to {bot_y_phys}")
else:
    bot_y_phys = H
    print(f"No blue line found; using full image (rows 0 to {H-1})")

def hough(mask, params):
    blurred = cv2.GaussianBlur(mask, (5, 5), 1)
    c = cv2.HoughCircles(blurred, cv2.HOUGH_GRADIENT, **params)
    return [] if c is None else [(int(x), int(y), int(r)) for x, y, r in c[0]]

# Detect ALL blues and greys in the band
r_min = max(4, int(6/scale))
r_max = max(10, int(18/scale))
blues_all = hough(blue_mask,  dict(dp=1, minDist=15, param1=80, param2=12, minRadius=r_min, maxRadius=r_max))
greys_all = hough(data_mask, dict(dp=1, minDist=12, param1=60, param2=12, minRadius=2, maxRadius=r_max))

blues = [b for b in blues_all if b[1] < bot_y_phys]
greys = [g for g in greys_all if g[1] < bot_y_phys]
# If using full image and got 0, lower the data threshold
if bot_y_phys == H and len(greys) < 200:
    print("Re-detecting with lower threshold to find more data dots…")
    data_mask2 = cv2.inRange(hsv, np.array((0, 0, 0)), np.array((180, 80, 230)))
    greys_all = hough(data_mask2, dict(dp=1, minDist=10, param1=50, param2=10, minRadius=2, maxRadius=r_max))
    greys = [g for g in greys_all if g[1] < bot_y_phys]

# Filter out greys that are AT a blue center (those are blue interiors, not data dots).
# User said NONE of the blues are aligned, so no real data dot is at a blue center.
CENTER_RADIUS = 8
blue_centers = [(b[0], b[1]) for b in blues]
data_dots = []
for g in greys:
    at_blue = any(math.hypot(g[0]-bx, g[1]-by) < CENTER_RADIUS for bx, by in blue_centers)
    if not at_blue:
        data_dots.append(g)
greys = data_dots
print(f"After removing blue-interior greys: {len(greys)} data dots")
print(f"\nBlues in band: {len(blues)}  Greys in band: {len(greys)}")

# Pair ALL blues to ALL greys with Hungarian (globally optimal)
n = min(len(blues), len(greys))
if n == 0:
    print("Nothing to pair", flush=True); sys.exit(1)

cost = np.full((len(blues), len(greys)), 1e6)
for i, (bx, by, _) in enumerate(blues):
    for j, (gx, gy, _) in enumerate(greys):
        cost[i, j] = math.hypot(bx-gx, by-gy)
row, col = linear_sum_assignment(cost)

pairs = []
for r, c in zip(row, col):
    if cost[r, c] < 1e5:
        bx, by, _ = blues[r]
        gx, gy, _ = greys[c]
        pairs.append({
            "dot":  [round(wx + bx/scale), round(wy + by/scale)],
            "spot": [round(wx + gx/scale), round(wy + gy/scale)],
        })
pairs.sort(key=lambda p: p["dot"][0])
dists = [math.hypot(p['spot'][0]-p['dot'][0], p['spot'][1]-p['dot'][1]) for p in pairs]
print(f"\nHungarian pairs: {len(pairs)}")
if dists:
    print(f"Distance: min={min(dists):.0f} max={max(dists):.0f} avg={sum(dists)/len(dists):.0f}")
    print(f"  >20: {sum(1 for d in dists if d>20)}  >50: {sum(1 for d in dists if d>50)}  >100: {sum(1 for d in dists if d>100)}")
    near = sum(1 for d in dists if d < 10)
    far = sum(1 for d in dists if d >= 50)
    print(f"  pairs with dist < 10 (already aligned?): {near}")
    print(f"  pairs with dist >= 50 (clearly misaligned): {far}")

with open("/Users/admin/opencode-imagestudio/targets.json", "w") as f:
    json.dump({"bounds": [wx, wy, ww, wh], "scale": scale,
               "valid_band": [wy, wy + bot_y_phys/scale], "pairs": pairs}, f, indent=2)
print("Saved targets.json")
