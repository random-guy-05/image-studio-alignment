"""Detect the BLUE RECTANGLE (top and bottom thin lines) that bounds the grid.
The valid band is BETWEEN those two lines.
Also: find blue circles inside the rectangle, and data dots inside the rectangle.
Then Hungarian pair and save."""
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

subprocess.run(["screencapture", "-R", f"{wx},{wy},{ww},{wh}", "/tmp/v8.png"], check=True)
img = cv2.imread("/tmp/v8.png")
H, W = img.shape[:2]
scale = W / ww
print(f"Image: {W}x{H}  scale={scale:.2f}x")

hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
blue_mask  = cv2.inRange(hsv, np.array((100, 120, 100)), np.array((130, 255, 255)))

# Find the LONGEST blue run per row — real rectangle edges have very long runs
longest_run = np.zeros(H, dtype=int)
for y in range(H):
    row = blue_mask[y] > 0
    if not row.any(): continue
    padded = np.concatenate(([False], row, [False]))
    diffs = np.diff(padded.astype(int))
    starts = np.where(diffs == 1)[0]
    ends = np.where(diffs == -1)[0]
    runs = ends - starts
    if len(runs): longest_run[y] = runs.max()

# A rectangle edge is a row where blue runs nearly the full width of the grid
# (e.g., > 60% of image width = > 734 for W=1224)
RECT_MIN_RUN = int(W * 0.4)  # 490 for 1224-wide
line_rows = np.where(longest_run >= RECT_MIN_RUN)[0]
print(f"Rows with longest_run >= {RECT_MIN_RUN}: {len(line_rows)}")
if len(line_rows) == 0:
    # Lower threshold
    RECT_MIN_RUN = int(W * 0.2)
    line_rows = np.where(longest_run >= RECT_MIN_RUN)[0]
    print(f"  Lowered to {RECT_MIN_RUN}: {len(line_rows)}")

# Cluster
if len(line_rows) == 0:
    print("No rectangle edges found!", flush=True); sys.exit(1)
clusters = [[line_rows[0]]]
for r in line_rows[1:]:
    if r - clusters[-1][-1] <= 3:
        clusters[-1].append(r)
    else:
        clusters.append([r])
clusters.sort(key=lambda c: -len(c))  # largest first

# Take the top 2 clusters as the rectangle top and bottom
top2 = sorted(clusters[:2], key=lambda c: c[0])
top_y = sum(top2[0]) // len(top2[0])
bot_y = sum(top2[1]) // len(top2[1])
print(f"Rectangle: top row ~{top_y}, bottom row ~{bot_y}  (band: {top_y} to {bot_y})")

# Now find blues and data dots INSIDE the rectangle
def hough(mask, params):
    blurred = cv2.GaussianBlur(mask, (5, 5), 1)
    c = cv2.HoughCircles(blurred, cv2.HOUGH_GRADIENT, **params)
    return [] if c is None else [(int(x), int(y), int(r)) for x, y, r in c[0]]

# Data dots: V < 180, S < 50 (catches black + dark grey, excludes blue interiors V>=220)
data_mask = cv2.inRange(hsv, np.array((0, 0, 0)), np.array((180, 50, 180)))

r_min = max(4, int(6/scale))
r_max = max(10, int(18/scale))
blues_all = hough(blue_mask,  dict(dp=1, minDist=15, param1=80, param2=12, minRadius=r_min, maxRadius=r_max))
greys_all = hough(data_mask, dict(dp=1, minDist=12, param1=60, param2=12, minRadius=2, maxRadius=r_max))

# Filter to inside the rectangle
blues = [b for b in blues_all if top_y < b[1] < bot_y]
greys = [g for g in greys_all if top_y < g[1] < bot_y]
print(f"Blues inside rectangle: {len(blues)}")
print(f"Greys inside rectangle: {len(greys)}")

# Pair with Hungarian
n = min(len(blues), len(greys))
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
    print(f"  pairs with dist < 15 (likely already aligned): {sum(1 for d in dists if d < 15)}")
    print(f"  pairs with dist >= 50 (clearly misaligned): {sum(1 for d in dists if d >= 50)}")

with open("/Users/admin/opencode-imagestudio/targets.json", "w") as f:
    json.dump({"bounds": [wx, wy, ww, wh], "scale": scale,
               "rect_band": [int(top_y), int(bot_y)], "pairs": pairs}, f, indent=2)
print("Saved targets.json")
