"""Detect the grid bounding box from the blue circles.
Use that as the band. Find blues and data dots inside."""
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

subprocess.run(["screencapture", "-R", f"{wx},{wy},{ww},{wh}", "/tmp/v9.png"], check=True)
img = cv2.imread("/tmp/v9.png")
H, W = img.shape[:2]
scale = W / ww
print(f"Image: {W}x{H}  scale={scale:.2f}x")

hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
blue_mask  = cv2.inRange(hsv, np.array((100, 120, 100)), np.array((130, 255, 255)))
data_mask  = cv2.inRange(hsv, np.array((0, 0, 0)), np.array((180, 50, 180)))

def hough(mask, params):
    blurred = cv2.GaussianBlur(mask, (5, 5), 1)
    c = cv2.HoughCircles(blurred, cv2.HOUGH_GRADIENT, **params)
    return [] if c is None else [(int(x), int(y), int(r)) for x, y, r in c[0]]

r_min = max(4, int(6/scale))
r_max = max(10, int(18/scale))
blues_all = hough(blue_mask,  dict(dp=1, minDist=15, param1=80, param2=12, minRadius=r_min, maxRadius=r_max))
greys_all = hough(data_mask, dict(dp=1, minDist=12, param1=60, param2=12, minRadius=2, maxRadius=r_max))

# Grid bounding box from blues
if not blues_all:
    print("No blues found!", flush=True); sys.exit(1)
xs = [b[0] for b in blues_all]
ys = [b[1] for b in blues_all]
# Use percentiles to be robust to outliers
x_lo, x_hi = int(np.percentile(xs, 2)), int(np.percentile(xs, 98))
y_lo, y_hi = int(np.percentile(ys, 2)), int(np.percentile(ys, 98))
# Add a margin
margin = 10
x_lo -= margin; x_hi += margin
y_lo -= margin; y_hi += margin
print(f"Grid bbox: x=[{x_lo},{x_hi}]  y=[{y_lo},{y_hi}]")

# Filter to inside grid
blues = [b for b in blues_all if x_lo < b[0] < x_hi and y_lo < b[1] < y_hi]
greys = [g for g in greys_all if x_lo < g[0] < x_hi and y_lo < g[1] < y_hi]
print(f"Blues in grid: {len(blues)}")
print(f"Greys in grid: {len(greys)}")

# Pair with Hungarian, constrained to reasonable distance
n = min(len(blues), len(greys))
cost = np.full((len(blues), len(greys)), 1e6)
for i, (bx, by, _) in enumerate(blues):
    for j, (gx, gy, _) in enumerate(greys):
        d = math.hypot(bx-gx, by-gy)
        # Reject pairings > 100pt (clearly wrong)
        cost[i, j] = d if d < 100 else 1e6
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
    print(f"  <15: {sum(1 for d in dists if d<15)}  15-50: {sum(1 for d in dists if 15<=d<50)}  50-100: {sum(1 for d in dists if 50<=d<100)}")

with open("/Users/admin/opencode-imagestudio/targets.json", "w") as f:
    json.dump({"bounds": [wx, wy, ww, wh], "scale": scale,
               "grid_bbox": [int(x_lo), int(y_lo), int(x_hi), int(y_hi)],
               "pairs": pairs}, f, indent=2)
print("Saved targets.json")
