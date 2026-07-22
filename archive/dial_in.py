"""Dial in the exact params to get ~220 grey circles."""
import cv2, numpy as np
import json, math

cap = cv2.imread("/tmp/imagestudio.png")
hsv = cv2.cvtColor(cap, cv2.COLOR_BGR2HSV)

# Try different light grey ranges
configs = [
    ((0, 0, 180), (180, 20, 240), 24),
    ((0, 0, 180), (180, 20, 240), 25),
    ((0, 0, 180), (180, 20, 240), 23),
    ((0, 0, 170), (180, 25, 235), 22),
    ((0, 0, 170), (180, 25, 235), 23),
    ((0, 0, 170), (180, 25, 235), 24),
    ((0, 0, 160), (180, 30, 230), 20),
    ((0, 0, 160), (180, 30, 230), 21),
    ((0, 0, 160), (180, 30, 230), 22),
]

best = None
for lo, hi, p2 in configs:
    mask = cv2.inRange(hsv, np.array(lo), np.array(hi))
    blurred = cv2.GaussianBlur(mask, (5, 5), 1)
    c = cv2.HoughCircles(blurred, cv2.HOUGH_GRADIENT, dp=1, minDist=20,
                         param1=80, param2=p2, minRadius=10, maxRadius=18)
    n = 0 if c is None else len(c[0])
    diff = abs(n - 220)
    print(f"  {lo}->{hi} p2={p2}: {n}  (diff from 220: {diff})")
    if best is None or diff < best[0]:
        best = (diff, n, lo, hi, p2)

print(f"\nBest: {best[1]} circles (diff {best[0]} from 220): {best[2]}->{best[3]} p2={best[4]}")

# Apply best config
lo, hi, p2 = best[2], best[3], best[4]
mask = cv2.inRange(hsv, np.array(lo), np.array(hi))
blurred = cv2.GaussianBlur(mask, (5, 5), 1)
c = cv2.HoughCircles(blurred, cv2.HOUGH_GRADIENT, dp=1, minDist=20,
                     param1=80, param2=p2, minRadius=10, maxRadius=18)
grey_circles = [] if c is None else [(int(x), int(y), int(r)) for x, y, r in c[0]]

# Get blue circles
blue_mask = cv2.inRange(hsv, np.array((100, 120, 100)), np.array((130, 255, 255)))
blurred_b = cv2.GaussianBlur(blue_mask, (5, 5), 1)
b_c = cv2.HoughCircles(blurred_b, cv2.HOUGH_GRADIENT, dp=1, minDist=20,
                        param1=80, param2=15, minRadius=12, maxRadius=18)
blue_circles = [] if b_c is None else [(int(x), int(y), int(r)) for x, y, r in b_c[0]]
print(f"\nBlue: {len(blue_circles)}  Grey: {len(grey_circles)}")

# Pair
data = json.load(open("/Users/admin/opencode-imagestudio/targets.json"))
bounds = data["bounds"]
scale = data["scale"]
ox, oy = bounds[0], bounds[1]

blue_pts = sorted([(ox + x/scale, oy + y/scale) for x, y, _ in blue_circles], key=lambda p: p[0])
grey_pts = sorted([(ox + x/scale, oy + y/scale) for x, y, _ in grey_circles], key=lambda p: p[0])

used = set()
pairs = []
for bx, by in blue_pts:
    best, best_d = None, float("inf")
    for j, (gx, gy) in enumerate(grey_pts):
        if j in used:
            continue
        d = math.hypot(bx - gx, by - gy)
        if d < best_d:
            best_d = d
            best = j
    if best is not None:
        used.add(best)
        gx, gy = grey_pts[best]
        pairs.append({"dot": [round(bx), round(by)], "spot": [round(gx), round(gy)]})

print(f"\nPaired {len(pairs)} dots")
dists = [math.hypot(p['spot'][0]-p['dot'][0], p['spot'][1]-p['dot'][1]) for p in pairs]
if dists:
    print(f"Distance: min={min(dists):.0f}  max={max(dists):.0f}  avg={sum(dists)/len(dists):.0f}")
    print(f"  >50: {sum(1 for d in dists if d > 50)}  >100: {sum(1 for d in dists if d > 100)}  >200: {sum(1 for d in dists if d > 200)}")

# Save
with open("/Users/admin/opencode-imagestudio/targets.json", "w") as f:
    json.dump({"bounds": list(bounds), "scale": scale, "pairs": pairs}, f, indent=2)
print(f"Updated targets.json with {len(pairs)} pairs")
