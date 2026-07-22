"""Detect the TWO thin blue lines by finding rows with the longest
consecutive run of blue pixels. Real lines are continuous in X;
circles are not (just left+right edges at each row)."""
import subprocess, json, math, sys
import cv2, numpy as np
from scipy.optimize import linear_sum_assignment

# Activate + capture
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

subprocess.run(["screencapture", "-R", f"{wx},{wy},{ww},{wh}", "/tmp/v4.png"], check=True)
img = cv2.imread("/tmp/v4.png")
H, W = img.shape[:2]
scale = W / ww
print(f"Image: {W}x{H}  scale={scale:.2f}x")

hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
blue_mask  = cv2.inRange(hsv, np.array((100, 120, 100)), np.array((130, 255, 255)))
grey_light = cv2.inRange(hsv, np.array((0, 0, 180)), np.array((180, 20, 240)))
grey_black = cv2.inRange(hsv, np.array((0, 0, 0)),   np.array((180, 60,  60)))

# For each row, find the LONGEST run of consecutive blue pixels
# A real line → long run (hundreds). A circle → short runs (10-30 each).
longest_run = np.zeros(H, dtype=int)
for y in range(H):
    row = blue_mask[y] > 0  # boolean
    if not row.any():
        continue
    # Find runs of True
    padded = np.concatenate(([False], row, [False]))
    diffs = np.diff(padded.astype(int))
    starts = np.where(diffs == 1)[0]
    ends = np.where(diffs == -1)[0]
    runs = ends - starts
    if len(runs):
        longest_run[y] = runs.max()

print(f"\nLongest blue run per row (top 20 by length):")
top_rows = np.argsort(longest_run)[-20:][::-1]
for r in sorted(top_rows):
    print(f"  row {r:4d}: longest_run={longest_run[r]}  total_blue={int(blue_mask[r].sum()/255)}")

# Find rows where longest_run is very large (real lines)
LINE_MIN_RUN = max(100, int(W * 0.3))  # at least 30% of image width as a single run
line_rows = np.where(longest_run >= LINE_MIN_RUN)[0]
print(f"\nRows with longest_run >= {LINE_MIN_RUN}: {len(line_rows)}")
if len(line_rows) > 0:
    print(f"  {line_rows}")

# Cluster consecutive line rows
if len(line_rows) == 0:
    print("No lines found!", flush=True); sys.exit(1)

clusters = [[line_rows[0]]]
for r in line_rows[1:]:
    if r - clusters[-1][-1] <= 3:
        clusters[-1].append(r)
    else:
        clusters.append([r])

line_bands = [(min(c), max(c)) for c in clusters]
line_bands.sort(key=lambda b: b[0])
print(f"\nDetected {len(line_bands)} THIN blue line band(s):")
for i, (lo, hi) in enumerate(line_bands):
    print(f"  line {i}: rows {lo}–{hi}  (mid={(lo+hi)//2})")

if len(line_bands) < 1:
    print(f"ERROR: no blue line found", flush=True); sys.exit(1)

# User said: only use dots ABOVE the (single) thin blue line
# So top of band = 0, bottom of band = the line
top_y_phys = 0
bot_y_phys = (line_bands[0][0] + line_bands[0][1]) // 2
print(f"\nValid band (rows): {top_y_phys} to {bot_y_phys}  (only above the blue line)")

# Detect circles
def hough(mask, params):
    blurred = cv2.GaussianBlur(mask, (5, 5), 1)
    c = cv2.HoughCircles(blurred, cv2.HOUGH_GRADIENT, **params)
    return [] if c is None else [(int(x), int(y), int(r)) for x, y, r in c[0]]

# At 1x scale, radii are smaller. Adjust for scale.
r_min = max(4, int(6 / scale))
r_max = max(10, int(18 / scale))
print(f"Radius bounds for scale {scale:.2f}: {r_min}-{r_max}")

blues_all  = hough(blue_mask,  dict(dp=1, minDist=20, param1=80, param2=15, minRadius=r_min, maxRadius=r_max))
greys_all  = hough(grey_light, dict(dp=1, minDist=20, param1=80, param2=25, minRadius=max(3, int(9/scale)),  maxRadius=r_max)) + \
             hough(grey_black, dict(dp=1, minDist=20, param1=80, param2=22, minRadius=max(3, int(9/scale)),  maxRadius=r_max))

blues = [b for b in blues_all if top_y_phys <= b[1] <= bot_y_phys]
greys = [g for g in greys_all if top_y_phys <= g[1] <= bot_y_phys]

# Filter greys inside any blue (ring interiors)
def in_ring(p, rings, pad=8):
    return any(math.hypot(p[0]-c[0], p[1]-c[1]) < pad for c in rings)
real_targets = [g for g in greys if not in_ring(g, blues)]

print(f"\nBlues in band:  {len(blues)} (of {len(blues_all)} total)")
print(f"Greys in band:  {len(greys)} (of {len(greys_all)} total)")
print(f"Real targets:   {len(real_targets)}")

n = min(len(blues), len(real_targets))
if n == 0:
    print("Nothing to pair", flush=True); sys.exit(1)

cost = np.full((len(blues), len(real_targets)), 1e6)
for i, (bx, by, _) in enumerate(blues):
    for j, (gx, gy, _) in enumerate(real_targets):
        cost[i, j] = math.hypot(bx-gx, by-gy)
row, col = linear_sum_assignment(cost)

pairs = []
for r, c in zip(row, col):
    if cost[r, c] < 1e5:
        bx, by, _ = blues[r]
        gx, gy, _ = real_targets[c]
        pairs.append({
            "dot":  [round(wx + bx/scale), round(wy + by/scale)],
            "spot": [round(wx + gx/scale), round(wy + gy/scale)],
        })
pairs.sort(key=lambda p: p["dot"][0])
dists = [math.hypot(p['spot'][0]-p['dot'][0], p['spot'][1]-p['dot'][1]) for p in pairs]
print(f"\nHungarian pairs: {len(pairs)}")
if dists:
    print(f"Distance: min={min(dists):.0f} max={max(dists):.0f} avg={sum(dists)/len(dists):.0f}")
    print(f"  >50: {sum(1 for d in dists if d>50)}  >100: {sum(1 for d in dists if d>100)}")

with open("/Users/admin/opencode-imagestudio/targets.json", "w") as f:
    json.dump({"bounds": [wx, wy, ww, wh], "scale": scale,
               "valid_band": [wy + top_y_phys/scale, wy + bot_y_phys/scale], "pairs": pairs}, f, indent=2)
print("Saved targets.json")
