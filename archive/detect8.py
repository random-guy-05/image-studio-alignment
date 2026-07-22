"""Detect the BLUE RECTANGLE (all 4 edges) that bounds the grid.
The valid area is STRICTLY inside the rectangle.
Find blues and data dots inside. Pair with Hungarian.
Then run alignment (which will also enforce the rectangle)."""
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

subprocess.run(["screencapture", "-R", f"{wx},{wy},{ww},{wh}", "/tmp/v10.png"], check=True)
img = cv2.imread("/tmp/v10.png")
H, W = img.shape[:2]
scale = W / ww
print(f"Image: {W}x{H}  scale={scale:.2f}x")

hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
blue_mask  = cv2.inRange(hsv, np.array((100, 120, 100)), np.array((130, 255, 255)))

# Find the rectangle: long horizontal and vertical blue runs
# A rectangle edge is a run that's long AND consistent
longest_h_run = np.zeros(H, dtype=int)
for y in range(H):
    row = blue_mask[y] > 0
    if not row.any(): continue
    padded = np.concatenate(([False], row, [False]))
    diffs = np.diff(padded.astype(int))
    starts = np.where(diffs == 1)[0]
    ends = np.where(diffs == -1)[0]
    runs = ends - starts
    if len(runs): longest_h_run[y] = runs.max()

longest_v_run = np.zeros(W, dtype=int)
for x in range(W):
    col = blue_mask[:, x] > 0
    if not col.any(): continue
    padded = np.concatenate(([False], col, [False]))
    diffs = np.diff(padded.astype(int))
    starts = np.where(diffs == 1)[0]
    ends = np.where(diffs == -1)[0]
    runs = ends - starts
    if len(runs): longest_v_run[x] = runs.max()

# Find rows with very long horizontal runs (= top/bottom edges of rectangle)
# Threshold: at least 30% of image width
H_MIN = int(W * 0.3)
h_edge_rows = np.where(longest_h_run >= H_MIN)[0]
print(f"Horizontal edge candidates (run >= {H_MIN}): {len(h_edge_rows)}")
# Find columns with very long vertical runs (= left/right edges)
V_MIN = int(H * 0.15)
v_edge_cols = np.where(longest_v_run >= V_MIN)[0]
print(f"Vertical edge candidates (run >= {V_MIN}): {len(v_edge_cols)}")

if len(h_edge_rows) < 2 or len(v_edge_cols) < 2:
    # Lower thresholds further
    H_MIN = int(W * 0.15)
    h_edge_rows = np.where(longest_h_run >= H_MIN)[0]
    V_MIN = int(H * 0.08)
    v_edge_cols = np.where(longest_v_run >= V_MIN)[0]
    print(f"  Lowered: h_edges={len(h_edge_rows)}  v_edges={len(v_edge_cols)}")

if len(h_edge_rows) < 2 or len(v_edge_cols) < 2:
    print(f"ERROR: can't find rectangle edges", flush=True); sys.exit(1)

# Cluster h_edge_rows into top and bottom
def cluster(arr):
    if len(arr) == 0: return []
    cs = [[arr[0]]]
    for v in arr[1:]:
        if v - cs[-1][-1] <= 3: cs[-1].append(v)
        else: cs.append([v])
    return [(min(c), max(c)) for c in cs]

h_bands = cluster(sorted(h_edge_rows))
v_bands = cluster(sorted(v_edge_cols))
print(f"Horizontal bands: {h_bands}")
print(f"Vertical bands:   {v_bands}")

# Take topmost h_band and bottommost as top/bottom edges
rect_top = h_bands[0][0]
rect_bot = h_bands[-1][1]
rect_left = v_bands[0][0]
rect_right = v_bands[-1][1]
print(f"Rectangle bounds: x=[{rect_left},{rect_right}]  y=[{rect_top},{rect_bot}]")

# Find blues and data dots INSIDE the rectangle
def hough(mask, params):
    blurred = cv2.GaussianBlur(mask, (5, 5), 1)
    c = cv2.HoughCircles(blurred, cv2.HOUGH_GRADIENT, **params)
    return [] if c is None else [(int(x), int(y), int(r)) for x, y, r in c[0]]

data_mask = cv2.inRange(hsv, np.array((0, 0, 0)), np.array((180, 50, 200)))
r_min = max(4, int(6/scale))
r_max = max(10, int(18/scale))
blues_all = hough(blue_mask,  dict(dp=1, minDist=15, param1=80, param2=12, minRadius=r_min, maxRadius=r_max))
greys_all = hough(data_mask, dict(dp=1, minDist=10, param1=50, param2=10, minRadius=2, maxRadius=r_max))

# STRICT: only inside the rectangle (with a 20pt margin to avoid the border)
M = 20
blues = [b for b in blues_all if rect_left+M < b[0] < rect_right-M and rect_top+M < b[1] < rect_bot-M]
greys = [g for g in greys_all if rect_left+M < g[0] < rect_right-M and rect_top+M < g[1] < rect_bot-M]
print(f"Blues inside rectangle: {len(blues)}")
print(f"Greys inside rectangle: {len(greys)}")

# Pair with Hungarian
n = min(len(blues), len(greys))
cost = np.full((len(blues), len(greys)), 1e6)
for i, (bx, by, _) in enumerate(blues):
    for j, (gx, gy, _) in enumerate(greys):
        d = math.hypot(bx-gx, by-gy)
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

# Save with rectangle bounds (in POINT coordinates for align.py)
with open("/Users/admin/opencode-imagestudio/targets.json", "w") as f:
    json.dump({"bounds": [wx, wy, ww, wh], "scale": scale,
               "rectangle": [int(wx + rect_left/scale), int(wy + rect_top/scale),
                             int(wx + rect_right/scale), int(wy + rect_bot/scale)],
               "pairs": pairs}, f, indent=2)
rx1, ry1, rx2, ry2 = wx+rect_left/scale, wy+rect_top/scale, wx+rect_right/scale, wy+rect_bot/scale
print(f"\nSaved targets.json with rectangle (points)=[{rx1:.0f},{ry1:.0f},{rx2:.0f},{ry2:.0f}]")
