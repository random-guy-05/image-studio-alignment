"""Detect the two blue horizontal lines that bound the valid region,
then re-detect blues and greys only WITHIN that band."""
import subprocess, json, math
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

subprocess.run(["screencapture", "-R", f"{wx},{wy},{ww},{wh}", "/tmp/v3.png"], check=True)
img = cv2.imread("/tmp/v3.png")
H, W = img.shape[:2]
scale = W / ww  # physical pixels per point (computed dynamically)
print(f"Image size: {W}x{H}  scale: {scale:.2f}x")
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
blue_mask  = cv2.inRange(hsv, np.array((100, 120, 100)), np.array((130, 255, 255)))
grey_light = cv2.inRange(hsv, np.array((0, 0, 180)), np.array((180, 20, 240)))
grey_black = cv2.inRange(hsv, np.array((0, 0, 0)),   np.array((180, 60,  60)))

# Find the two blue horizontal lines by counting blue pixels per row
row_blue = blue_mask.sum(axis=1) / 255  # blue pixels per row
# Threshold: 100 blue pixels per row. Real thin lines have 200+; noise has <30.
threshold = 100
line_rows = np.where(row_blue > threshold)[0]
print(f"Blue rows above {threshold:.0f}: {len(line_rows)} (e.g. first 5: {line_rows[:5]})")

# Cluster consecutive line rows into line regions
if len(line_rows) == 0:
    print("No blue lines detected!", flush=True)
    import sys; sys.exit(1)

clusters = []
current = [line_rows[0]]
for r in line_rows[1:]:
    if r - current[-1] <= 3:
        current.append(r)
    else:
        clusters.append(current)
        current = [r]
clusters.append(current)

# Each cluster is a horizontal line band. THIN lines only (≤5 rows).
THIN_MAX = 5
line_bands = [(min(c), max(c)) for c in clusters if (max(c) - min(c) + 1) <= THIN_MAX]
line_bands.sort(key=lambda b: b[0])
print(f"Detected {len(line_bands)} THIN blue line band(s) (≤ {THIN_MAX} rows):")
for i, (lo, hi) in enumerate(line_bands):
    print(f"  line {i}: rows {lo}–{hi}  (mid={(lo+hi)//2})")

if len(line_bands) < 2:
    print(f"ERROR: need exactly 2 thin blue lines, found {len(line_bands)}", flush=True)
    import sys; sys.exit(1)

# Valid region: between the top and bottom thin lines
top_y_phys = (line_bands[0][0] + line_bands[0][1]) // 2
bot_y_phys = (line_bands[-1][0] + line_bands[-1][1]) // 2
print(f"\nValid band (phys px rows): {top_y_phys} to {bot_y_phys}")
# Convert to points (relative to window)
top_y_pt = wy + top_y_phys / scale
bot_y_pt = wy + bot_y_phys / scale
print(f"Valid band (points):       {top_y_pt:.0f} to {bot_y_pt:.0f}")

# Detect circles
def hough(mask, params):
    blurred = cv2.GaussianBlur(mask, (5, 5), 1)
    c = cv2.HoughCircles(blurred, cv2.HOUGH_GRADIENT, **params)
    return [] if c is None else [(int(x), int(y), int(r)) for x, y, r in c[0]]

blues_all  = hough(blue_mask,  dict(dp=1, minDist=20, param1=80, param2=15, minRadius=12, maxRadius=18))
greys_all  = hough(grey_light, dict(dp=1, minDist=20, param1=80, param2=25, minRadius=9,  maxRadius=18)) + \
             hough(grey_black, dict(dp=1, minDist=20, param1=80, param2=22, minRadius=9,  maxRadius=18))

# Filter to valid band
blues = [b for b in blues_all if top_y_phys <= b[1] <= bot_y_phys]
greys = [g for g in greys_all if top_y_phys <= g[1] <= bot_y_phys]

# Also filter out greys INSIDE any blue (ring interiors)
def in_ring(p, rings, pad=15):
    return any(math.hypot(p[0]-c[0], p[1]-c[1]) < pad for c in rings)

real_targets = [g for g in greys if not in_ring(g, blues)]
print(f"\nBlues in band:  {len(blues)} (of {len(blues_all)} total)")
print(f"Greys in band:  {len(greys)} (of {len(greys_all)} total)")
print(f"Real targets (not in any blue): {len(real_targets)}")

# Hungarian pairing
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

# Save
with open("/Users/admin/opencode-imagestudio/targets.json", "w") as f:
    json.dump({"bounds": [wx, wy, ww, wh], "scale": scale,
               "valid_band": [top_y_pt, bot_y_pt], "pairs": pairs}, f, indent=2)
print("Saved targets.json")
