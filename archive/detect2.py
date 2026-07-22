"""Filter out greys that are inside current blue rings.
The 'real' target spots are greys/blacks NOT close to any blue circle.
"""
import subprocess, json, math
import cv2, numpy as np
from scipy.optimize import linear_sum_assignment

# Get window
out = subprocess.check_output(["osascript", "-e",
    'tell application "System Events" to tell process "ImageStudio" to get position of front window & size of front window'
]).decode().strip()
nums = [int(x.strip()) for x in out.replace("{","").replace("}","").split(",")]
wx, wy, ww, wh = nums
print(f"Window: ({wx},{wy}) {ww}x{wh}")

subprocess.run(["screencapture", "-R", f"{wx},{wy},{ww},{wh}", "/tmp/cur.png"], check=True)
img = cv2.imread("/tmp/cur.png")
scale = 2.0
H, W = img.shape[:2]

hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
blue_mask  = cv2.inRange(hsv, np.array((100, 120, 100)), np.array((130, 255, 255)))
grey_light = cv2.inRange(hsv, np.array((0, 0, 180)), np.array((180, 20, 240)))
grey_black = cv2.inRange(hsv, np.array((0, 0, 0)),   np.array((180, 60,  60)))

def hough(mask, params):
    blurred = cv2.GaussianBlur(mask, (5, 5), 1)
    c = cv2.HoughCircles(blurred, cv2.HOUGH_GRADIENT, **params)
    return [] if c is None else [(int(x), int(y), int(r)) for x, y, r in c[0]]

blues = hough(blue_mask, dict(dp=1, minDist=20, param1=80, param2=15, minRadius=12, maxRadius=18))
light = hough(grey_light, dict(dp=1, minDist=20, param1=80, param2=25, minRadius=9, maxRadius=18))
black = hough(grey_black, dict(dp=1, minDist=20, param1=80, param2=22, minRadius=9, maxRadius=18))
all_greys = light + black

# Convert to points
blues_pt = [(wx + x/scale, wy + y/scale) for x, y, _ in blues]
greys_pt = [(wx + x/scale, wy + y/scale) for x, y, _ in all_greys]

print(f"Blues: {len(blues_pt)}")
print(f"All greys (light+black): {len(greys_pt)}")

# Filter out greys that are INSIDE a blue ring (within ~20 points of a blue center)
RING_INTERIOR_RADIUS = 20  # points
real_targets = []
ring_interiors = []
for gx, gy in greys_pt:
    inside_ring = False
    for bx, by in blues_pt:
        if math.hypot(gx-bx, gy-by) < RING_INTERIOR_RADIUS:
            inside_ring = True
            break
    if inside_ring:
        ring_interiors.append((gx, gy))
    else:
        real_targets.append((gx, gy))

print(f"Greys inside blue rings (NOT targets): {len(ring_interiors)}")
print(f"Greys NOT inside any blue ring (REAL TARGETS): {len(real_targets)}")

# Hungarian: pair blues to real targets
n = min(len(blues_pt), len(real_targets))
if n == 0:
    print("No real targets found!", flush=True)
else:
    cost = np.full((len(blues_pt), len(real_targets)), 1e6, dtype=np.float64)
    for i, (bx, by) in enumerate(blues_pt):
        for j, (gx, gy) in enumerate(real_targets):
            cost[i, j] = math.hypot(bx-gx, by-gy)
    row, col = linear_sum_assignment(cost)
    pairs = []
    for r, c in zip(row, col):
        if cost[r, c] < 1e5:
            pairs.append({"dot": [round(blues_pt[r][0]), round(blues_pt[r][1])],
                          "spot": [round(real_targets[c][0]), round(real_targets[c][1])]})
    pairs.sort(key=lambda p: p["dot"][0])
    dists = [math.hypot(p['spot'][0]-p['dot'][0], p['spot'][1]-p['dot'][1]) for p in pairs]
    print(f"\nHungarian pairs: {len(pairs)}")
    if dists:
        print(f"Distance stats: min={min(dists):.0f} max={max(dists):.0f} avg={sum(dists)/len(dists):.0f}")
        print(f"  >50: {sum(1 for d in dists if d>50)}  >100: {sum(1 for d in dists if d>100)}  >200: {sum(1 for d in dists if d>200)}")
    with open("/Users/admin/opencode-imagestudio/targets.json", "w") as f:
        json.dump({"bounds": [wx, wy, ww, wh], "scale": scale, "pairs": pairs}, f, indent=2)
    print("Wrote targets.json")
