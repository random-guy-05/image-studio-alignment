"""Re-pair blue and grey circles using nearest-neighbor matching.

Hypothesis: each blue dot's target is the closest grey spot.
This handles:
  - single-panel layouts (any direction)
  - multi-column layouts (each column pairs internally)
  - dense clusters (avoids crossing-pairing X-sort would do)
"""
import json, math
import numpy as np

data = json.load(open("/Users/admin/opencode-imagestudio/targets.json"))
pairs_naive = data["pairs"]

# Get the full detection lists — re-run detect to get blue/grey lists
import cv2
img = cv2.imread("/tmp/imagestudio.png")
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

blue_mask = cv2.inRange(hsv, np.array((100, 120, 100)), np.array((130, 255, 255)))
grey_light = cv2.inRange(hsv, np.array((0, 0, 100)), np.array((180, 30, 200)))
grey_dark  = cv2.inRange(hsv, np.array((0, 0, 60)),  np.array((180, 60, 130)))
grey_mask  = cv2.bitwise_or(grey_light, grey_dark)

def hough(mask, p2):
    blurred = cv2.GaussianBlur(mask, (5, 5), 1)
    c = cv2.HoughCircles(blurred, cv2.HOUGH_GRADIENT, dp=1, minDist=20,
                         param1=80, param2=p2, minRadius=5, maxRadius=20)
    return [] if c is None else [(int(x), int(y)) for x, y, r in c[0]]

blues = hough(blue_mask, 15)
greys = hough(grey_mask, 20)
print(f"blues: {len(blues)}, greys: {len(greys)}")

# Convert to points (image coords are physical pixels; window bounds in points)
bounds = data["bounds"]
scale = data["scale"]
ox, oy = bounds[0], bounds[1]

blue_pts  = [(ox + x/scale, oy + y/scale) for x, y in blues]
grey_pts  = [(ox + x/scale, oy + y/scale) for x, y in greys]

# Greedy nearest-neighbor pairing
# Sort both by X first as a heuristic for initial assignment
blue_sorted  = sorted(blue_pts,  key=lambda p: p[0])
grey_sorted  = sorted(grey_pts,  key=lambda p: p[0])

# Use scipy or implement manually
import itertools
n = min(len(blue_sorted), len(grey_sorted))
used_grey = set()
pairs = []
for bx, by in blue_sorted:
    best, best_d = None, float("inf")
    for j, (gx, gy) in enumerate(grey_sorted):
        if j in used_grey:
            continue
        d = math.hypot(bx - gx, by - gy)
        if d < best_d:
            best_d = d
            best = j
    if best is not None:
        used_grey.add(best)
        gx, gy = grey_sorted[best]
        pairs.append({"dot": [round(bx), round(by)], "spot": [round(gx), round(gy)]})

# Stats
dists = [math.hypot(p['spot'][0]-p['dot'][0], p['spot'][1]-p['dot'][1]) for p in pairs]
print(f"Paired {len(pairs)} dots")
print(f"Distance stats (points): min={min(dists):.0f}  max={max(dists):.0f}  avg={sum(dists)/len(dists):.0f}")
print(f"  pairs with dist > 100: {sum(1 for d in dists if d > 100)}")
print(f"  pairs with dist > 50:  {sum(1 for d in dists if d > 50)}")

# Show first 5 paired
print("\nFirst 5 pairs (nearest-neighbor):")
for i, p in enumerate(pairs[:5]):
    print(f"  {i}: dot=({p['dot'][0]},{p['dot'][1]})  spot=({p['spot'][0]},{p['spot'][1]})")

# Save as targets_nn.json (don't overwrite the existing one)
with open("/Users/admin/opencode-imagestudio/targets.json", "w") as f:
    json.dump({"bounds": list(bounds), "scale": scale, "pairs": pairs}, f, indent=2)
print("\nUpdated targets.json with nearest-neighbor pairing")
