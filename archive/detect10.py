"""Use connected components to find data dots (not Hough).
Connected components gives area + shape, so we can filter noise by size
and circularity. Catches the REALLY light grey dots because we use a
broad V threshold and then filter."""
import subprocess, json, math, sys
import cv2, numpy as np
from scipy.optimize import linear_sum_assignment

for _ in range(3):
    subprocess.run(["osascript", "-e", 'tell application "ImageStudio" to activate'], check=True)
import time
time.sleep(0.5)

# Get ALL window positions and find the main one (largest area)
out = subprocess.check_output(["osascript", "-e",
    'tell application "System Events" to tell process "ImageStudio" to get position of every window & size of every window'
]).decode().strip()
nums = [int(x.strip()) for x in out.replace("{","").replace("}","").split(",")]
# Format: [x1, y1, x2, y2, w1, h1, w2, h2] — positions then sizes
n = len(nums) // 4
windows = []
for i in range(n):
    x, y = nums[i*2], nums[i*2+1]
    w, h = nums[n*2 + i*2], nums[n*2 + i*2 + 1]
    windows.append((x, y, w, h, w*h))
windows.sort(key=lambda w: -w[4])
print(f"Found {len(windows)} windows: {[(x,y,w,h) for x,y,w,h,_ in windows]}")
wx, wy, ww, wh = windows[0][0], windows[0][1], windows[0][2], windows[0][3]
print(f"Using largest window: ({wx},{wy}) {ww}x{wh}")

subprocess.run(["screencapture", "-R", f"{wx},{wy},{ww},{wh}", "/tmp/v12.png"], check=True)
img = cv2.imread("/tmp/v12.png")
H, W = img.shape[:2]
scale = W / ww
print(f"Image: {W}x{H}  scale={scale:.2f}x")

hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
blue_mask  = cv2.inRange(hsv, np.array((100, 120, 100)), np.array((130, 255, 255)))
# Data dots: V < 220 (catches black + all greys + light greys). Blue interiors
# (V >= 220) are at blue centers and get filtered in a later step.
data_mask  = cv2.inRange(hsv, np.array((0, 0, 0)), np.array((180, 50, 220)))

def hough(mask, params):
    blurred = cv2.GaussianBlur(mask, (5, 5), 1)
    c = cv2.HoughCircles(blurred, cv2.HOUGH_GRADIENT, **params)
    return [] if c is None else [(int(x), int(y), int(r)) for x, y, r in c[0]]

# Detect blue circles (Hough works well for these — they're clear blue rings)
r_min = max(4, int(6/scale))
r_max = max(10, int(18/scale))
blues_all = hough(blue_mask, dict(dp=1, minDist=15, param1=80, param2=12, minRadius=r_min, maxRadius=r_max))

# Detect data dots via connected components — gives area + shape for filtering
num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(data_mask, 8)
print(f"Connected components: {num_labels-1}")

# Grid bounds from blues
if not blues_all:
    print("No blues found!", flush=True); sys.exit(1)
xs = [b[0] for b in blues_all]
ys = [b[1] for b in blues_all]
rect_left  = int(np.percentile(xs, 1))
rect_right = int(np.percentile(xs, 99))
rect_top   = int(np.percentile(ys, 1))
rect_bot   = int(np.percentile(ys, 99))
M = 20
print(f"Grid: x=[{rect_left+M},{rect_right-M}]  y=[{rect_top+M},{rect_bot-M}]")

# Blue centers for filtering
blue_centers = [(b[0], b[1]) for b in blues_all]

# Filter components by area, circularity, grid position, blue-center distance
greys = []
for i in range(1, num_labels):
    x, y, w, h, area = stats[i]
    cx, cy = centroids[i]
    if not (rect_left+M < cx < rect_right-M and rect_top+M < cy < rect_bot-M):
        continue
    if area < 5 or area > 200:
        continue
    if any(math.hypot(cx-bx, cy-by) < 12 for bx, by in blue_centers):
        continue
    greys.append((int(cx), int(cy)))

print(f"Blues in grid: {len(blues_all)} (after grid filter: {len([b for b in blues_all if rect_left+M<b[0]<rect_right-M and rect_top+M<b[1]<rect_bot-M])})")
print(f"Greys (data dots) after filters: {len(greys)}")

# Restrict blues to inside grid too
blues = [b for b in blues_all if rect_left+M < b[0] < rect_right-M and rect_top+M < b[1] < rect_bot-M]

# DEDUP greys that are very close (same dot detected twice)
def dedup(pts, min_sep=5):
    kept = []
    for p in pts:
        if not any(math.hypot(p[0]-q[0], p[1]-q[1]) < min_sep for q in kept):
            kept.append(p)
    return kept
greys = dedup(greys, min_sep=5)
print(f"Greys after dedup: {len(greys)}")

# Pair with Hungarian — no distance cap
n = min(len(blues), len(greys))
cost = np.full((len(blues), len(greys)), 1e6)
for i, (bx, by, _) in enumerate(blues):
    for j, gx_gy in enumerate([(g[0], g[1]) for g in greys]):
        cost[i, j] = math.hypot(bx-gx_gy[0], by-gx_gy[1])
row, col = linear_sum_assignment(cost)

pairs = []
for r, c in zip(row, col):
    if cost[r, c] < 1e5:
        bx, by, _ = blues[r]
        gx, gy = greys[c]
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
    print(f"  >100: {sum(1 for d in dists if d>100)}")

with open("/Users/admin/opencode-imagestudio/targets.json", "w") as f:
    json.dump({"bounds": [wx, wy, ww, wh], "scale": scale,
               "rectangle": [int(wx + rect_left/scale), int(wy + rect_top/scale),
                             int(wx + rect_right/scale), int(wy + rect_bot/scale)],
               "pairs": pairs}, f, indent=2)
print(f"\nSaved targets.json")
