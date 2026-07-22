"""Detect ALL circles, then categorize by color (blue vs grey)."""
import cv2, numpy as np
import json, math

cap = cv2.imread("/tmp/imagestudio.png")
gray = cv2.cvtColor(cap, cv2.COLOR_BGR2GRAY)
hsv = cv2.cvtColor(cap, cv2.COLOR_BGR2HSV)

# Detect all circles via Canny + Hough
edges = cv2.Canny(gray, 50, 150)
all_circles = cv2.HoughCircles(edges, cv2.HOUGH_GRADIENT, dp=1, minDist=20,
                                param1=50, param2=22, minRadius=10, maxRadius=18)
all_circles = [] if all_circles is None else [(int(x), int(y), int(r)) for x, y, r in all_circles[0]]
print(f"All circles detected: {len(all_circles)}")

# For each circle, sample pixels at its center to determine color
blue_mask = cv2.inRange(hsv, np.array((100, 120, 100)), np.array((130, 255, 255)))
grey_light = cv2.inRange(hsv, np.array((0, 0, 100)), np.array((180, 30, 200)))
grey_dark  = cv2.inRange(hsv, np.array((0, 0, 60)),  np.array((180, 60, 130)))
grey_mask  = cv2.bitwise_or(grey_light, grey_dark)

def sample_color(cx, cy, r):
    """Count how many pixels in the circle's area are blue vs grey."""
    x0, y0 = max(0, cx - r), max(0, cy - r)
    x1, y1 = min(blue_mask.shape[1], cx + r), min(blue_mask.shape[0], cy + r)
    blue_count = int(blue_mask[y0:y1, x0:x1].sum() / 255)
    grey_count = int(grey_mask[y0:y1, x0:x1].sum() / 255)
    total = (x1 - x0) * (y1 - y0)
    return blue_count, grey_count, total

blues, greys, others = [], [], []
for cx, cy, r in all_circles:
    b, g, total = sample_color(cx, cy, r)
    if b > g and b > 30:
        blues.append((cx, cy, r))
    elif g > b and g > 30:
        greys.append((cx, cy, r))
    else:
        others.append((cx, cy, r))

print(f"  categorized as blue: {len(blues)}")
print(f"  categorized as grey: {len(greys)}")
print(f"  others:              {len(others)}")

# Now pair: for each blue, find nearest grey (greedy)
data = json.load(open("/Users/admin/opencode-imagestudio/targets.json"))
bounds = data["bounds"]
scale = data["scale"]
ox, oy = bounds[0], bounds[1]

blue_pts = sorted([(ox + x/scale, oy + y/scale) for x, y, _ in blues], key=lambda p: p[0])
grey_pts = sorted([(ox + x/scale, oy + y/scale) for x, y, _ in greys], key=lambda p: p[0])

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
    if best is not None and best_d < 200:  # skip absurd pairings
        used.add(best)
        gx, gy = grey_pts[best]
        pairs.append({"dot": [round(bx), round(by)], "spot": [round(gx), round(gy)]})

print(f"\nPaired {len(pairs)} dots (after filtering distance > 200)")
dists = [math.hypot(p['spot'][0]-p['dot'][0], p['spot'][1]-p['dot'][1]) for p in pairs]
if dists:
    print(f"Distance: min={min(dists):.0f}  max={max(dists):.0f}  avg={sum(dists)/len(dists):.0f}")
    print(f"  >50 pts: {sum(1 for d in dists if d > 50)}  >100 pts: {sum(1 for d in dists if d > 100)}")

with open("/Users/admin/opencode-imagestudio/targets.json", "w") as f:
    json.dump({"bounds": list(bounds), "scale": scale, "pairs": pairs}, f, indent=2)
print(f"Updated targets.json")
