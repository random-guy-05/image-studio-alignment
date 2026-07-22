"""Use the blue circles' grid bounds as the valid area.
Find blues and data dots inside. Pair with Hungarian.
Also detect the actual blue rectangle as a secondary check.
Save with the grid bounds for align.py to enforce."""
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

subprocess.run(["screencapture", "-R", f"{wx},{wy},{ww},{wh}", "/tmp/v11.png"], check=True)
img = cv2.imread("/tmp/v11.png")
H, W = img.shape[:2]
scale = W / ww
print(f"Image: {W}x{H}  scale={scale:.2f}x")

hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
blue_mask  = cv2.inRange(hsv, np.array((100, 120, 100)), np.array((130, 255, 255)))
# Broad data-dot detection: V < 220 catches EVERYTHING dark (black + dark grey
# + medium grey + light grey + really light grey). We then filter out blue
# interiors (which are at blue center positions) in a later step.
data_mask  = cv2.inRange(hsv, np.array((0, 0, 0)), np.array((180, 50, 220)))

def hough(mask, params):
    blurred = cv2.GaussianBlur(mask, (5, 5), 1)
    c = cv2.HoughCircles(blurred, cv2.HOUGH_GRADIENT, **params)
    return [] if c is None else [(int(x), int(y), int(r)) for x, y, r in c[0]]

r_min = max(4, int(6/scale))
r_max = max(10, int(18/scale))
blues_all = hough(blue_mask,  dict(dp=1, minDist=15, param1=80, param2=12, minRadius=r_min, maxRadius=r_max))
greys_all = hough(data_mask, dict(dp=1, minDist=10, param1=50, param2=10, minRadius=2, maxRadius=r_max))

if not blues_all:
    print("No blues found!", flush=True); sys.exit(1)

# Grid bounds from blue circles (tight: 1st-99th percentile)
xs = [b[0] for b in blues_all]
ys = [b[1] for b in blues_all]
rect_left  = int(np.percentile(xs, 1))
rect_right = int(np.percentile(xs, 99))
rect_top   = int(np.percentile(ys, 1))
rect_bot   = int(np.percentile(ys, 99))
print(f"Grid bounds: x=[{rect_left},{rect_right}]  y=[{rect_top},{rect_bot}]")

# STRICT: only inside the grid (with 20pt margin to avoid the border)
M = 20
blues = [b for b in blues_all if rect_left+M < b[0] < rect_right-M and rect_top+M < b[1] < rect_bot-M]
greys_raw = [g for g in greys_all if rect_left+M < g[0] < rect_right-M and rect_top+M < g[1] < rect_bot-M]
print(f"Blues inside grid (20pt margin): {len(blues)}")
print(f"Greys inside grid (20pt margin, raw): {len(greys_raw)}")

# DEDUP greys that are very close (< 6pt) — they're the same dot detected twice
def dedup(pts, min_sep=6):
    kept = []
    for p in pts:
        if not any(math.hypot(p[0]-q[0], p[1]-q[1]) < min_sep for q in kept):
            kept.append(p)
    return kept
greys_dedup = dedup(greys_raw, min_sep=6)
print(f"Greys after dedup (min_sep=6): {len(greys_dedup)}")

# REMOVE greys that are AT a blue center (those are blue interiors, not data dots).
# The user said NONE of the blues are currently aligned, so no real data dot
# should be at a blue center. Greys at blue centers are just the ring interiors.
blue_centers = [(b[0], b[1]) for b in blues]
greys = [g for g in greys_dedup
         if not any(math.hypot(g[0]-bx, g[1]-by) < 12 for bx, by in blue_centers)]
print(f"Greys after removing blue-interiors: {len(greys)}")

# Pair with Hungarian — no distance cap, let it find the best matches
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
    print(f"  <15: {sum(1 for d in dists if d<15)}  15-50: {sum(1 for d in dists if 15<=d<50)}  50-100: {sum(1 for d in dists if 50<=d<100)}")

# Save with grid bounds (in POINT coordinates for align.py)
with open("/Users/admin/opencode-imagestudio/targets.json", "w") as f:
    json.dump({"bounds": [wx, wy, ww, wh], "scale": scale,
               "rectangle": [int(wx + rect_left/scale), int(wy + rect_top/scale),
                             int(wx + rect_right/scale), int(wy + rect_bot/scale)],
               "pairs": pairs}, f, indent=2)
rx1, ry1, rx2, ry2 = wx+rect_left/scale, wy+rect_top/scale, wx+rect_right/scale, wy+rect_bot/scale
print(f"\nSaved targets.json with grid bounds (points)=[{rx1:.0f},{ry1:.0f},{rx2:.0f},{ry2:.0f}]")
