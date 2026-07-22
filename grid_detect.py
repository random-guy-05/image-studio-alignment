"""Detect the GRID structure of the data dots.
Cytokine arrays are printed in a regular grid. If we find the grid spacing,
we can predict every dot position and just check if a dot exists there.
This eliminates false positives (gaps) and finds faint dots (we look at
specific positions, not everywhere)."""
import json
import cv2, numpy as np
import math
from collections import Counter, defaultdict
from scipy.signal import find_peaks

img = cv2.imread("screenshots/dots.png")
H, W = img.shape[:2]
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

# Find rectangle (same as before)
blue_mask = cv2.inRange(hsv, np.array((100, 120, 100)), np.array((130, 255, 255)))
h_mask = np.zeros_like(blue_mask)
for y in range(H):
    row = blue_mask[y] > 0
    if not row.any(): continue
    padded = np.concatenate(([False], row, [False]))
    diffs = np.diff(padded.astype(int))
    starts = np.where(diffs == 1)[0]; ends = np.where(diffs == -1)[0]
    for s, e in zip(starts, ends):
        if e - s > 200: h_mask[y, s:e] = 255
v_mask = np.zeros_like(blue_mask)
for x in range(W):
    col = blue_mask[:, x] > 0
    if not col.any(): continue
    padded = np.concatenate(([False], col, [False]))
    diffs = np.diff(padded.astype(int))
    starts = np.where(diffs == 1)[0]; ends = np.where(diffs == -1)[0]
    for s, e in zip(starts, ends):
        if e - s > 100: v_mask[s:e, x] = 255
corners = cv2.bitwise_and(h_mask, v_mask)
EDGE_EXCLUDE = 100
ys, xs = np.where(corners > 0)
clusters = defaultdict(list)
for y, x in zip(ys, xs):
    if x < EDGE_EXCLUDE or x > W - EDGE_EXCLUDE: continue
    if y < EDGE_EXCLUDE or y > H - EDGE_EXCLUDE: continue
    clusters[(y//20, x//20)].append((y, x))
centers = []
for key, pts in clusters.items():
    cy = sum(p[0] for p in pts) / len(pts)
    cx = sum(p[1] for p in pts) / len(pts)
    centers.append((cx, cy))
rect_left = int(min(c[0] for c in centers))
rect_right = int(max(c[0] for c in centers))
rect_top = int(min(c[1] for c in centers))
rect_bot = int(max(c[1] for c in centers))
print(f"Rectangle: x=[{rect_left},{rect_right}]  y=[{rect_top},{rect_bot}]  ({rect_right-rect_left}x{rect_bot-rect_top})")

# Get dark pixels inside the rectangle.
# Use a slightly broader mask for circle proposal, then strict center checks
# to avoid false positives.
data_mask = cv2.inRange(hsv, np.array((0, 0, 0)), np.array((180, 50, 215)))
data_mask[:rect_top, :] = 0; data_mask[rect_bot:, :] = 0
data_mask[:, :rect_left] = 0; data_mask[:, rect_right:] = 0

strict_mask = cv2.inRange(hsv, np.array((0, 0, 0)), np.array((180, 60, 190)))
strict_mask[:rect_top, :] = 0; strict_mask[rect_bot:, :] = 0
strict_mask[:, :rect_left] = 0; strict_mask[:, rect_right:] = 0

# Also build a broad mask for checking grid positions (catches faint dots)
broad_mask = cv2.inRange(hsv, np.array((0, 0, 0)), np.array((180, 80, 250)))
broad_mask[:rect_top, :] = 0; broad_mask[rect_bot:, :] = 0
broad_mask[:, :rect_left] = 0; broad_mask[:, rect_right:] = 0

# Find blobs with HoughCircles (conservative: no false positives, FN acceptable)
blurred = cv2.GaussianBlur(data_mask, (5, 5), 1)
circles = cv2.HoughCircles(
    blurred,
    cv2.HOUGH_GRADIENT,
    dp=1,
    minDist=15,
    param1=80,
    param2=12,
    minRadius=3,
    maxRadius=15,
)

raw_blobs = []
if circles is not None:
    for x, y, r in circles[0]:
        cx, cy, rr = int(round(x)), int(round(y)), int(round(r))
        if not (rect_left < cx < rect_right and rect_top < cy < rect_bot):
            continue
        if rr <= 0:
            continue

        pseudo_area = int(round(math.pi * rr * rr))
        raw_blobs.append((cx, cy, pseudo_area, rr, int(hsv[cy, cx, 2])))

# Deduplicate nearby detections: keep the darker-center one.
raw_blobs.sort(key=lambda b: (b[4], -b[3]))
dedup = []
for cx, cy, area, rr, center_v in raw_blobs:
    if any(abs(cx - ex) <= 4 and abs(cy - ey) <= 4 for ex, ey, _, _, _ in dedup):
        continue
    dedup.append((cx, cy, area, rr, center_v))

blobs = [(b[0], b[1], b[2]) for b in dedup]
print(f"Hough blobs inside rectangle (strict): {len(blobs)}")

# Infer the ten row bands without assuming even vertical spacing.
ROW_COUNT = 10
COL_COUNT = 24
anchor_y = np.sort(np.array([b[1] for b in blobs], dtype=float))
n = len(anchor_y)
dp = np.full((ROW_COUNT + 1, n + 1), np.inf)
prev = np.full((ROW_COUNT + 1, n + 1), -1, dtype=int)
dp[0, 0] = 0
for k in range(1, ROW_COUNT + 1):
    for end in range(k, n + 1):
        for start in range(k - 1, end):
            group = anchor_y[start:end]
            center = np.median(group)
            span = group[-1] - group[0]
            cost = np.sum((group - center) ** 2) + 1000 * max(0, span - 16) ** 2
            value = dp[k - 1, start] + cost
            if value < dp[k, end]:
                dp[k, end] = value
                prev[k, end] = start

row_groups = []
end = n
for k in range(ROW_COUNT, 0, -1):
    start = prev[k, end]
    row_groups.append(anchor_y[start:end])
    end = start
row_groups.reverse()
row_y = [int(round(np.median(group))) for group in row_groups]
print(f"\nRows: {row_y}")
print(f"Row gaps: {[row_y[i + 1] - row_y[i] for i in range(len(row_y) - 1)]}")

# Accumulate darkness around each anchor row. Local peaks recover the 24
# columns even when their gaps vary between subgrids.
darkness = np.clip(225 - hsv[:, :, 2].astype(float), 0, 225)
x_profile = np.zeros(W, dtype=float)
for cy in row_y:
    y0, y1 = max(0, cy - 8), min(H, cy + 9)
    x_profile += darkness[y0:y1, :].sum(axis=0)
x_profile[:rect_left] = 0
x_profile[rect_right:] = 0
baseline = cv2.GaussianBlur(x_profile.reshape(1, -1), (0, 0), 12).ravel()
x_profile = np.maximum(x_profile - baseline, 0)

anchor_min_x = min(b[0] for b in blobs)
anchor_max_x = max(b[0] for b in blobs)
peak_min_x = max(rect_left, anchor_min_x - 8)
peak_max_x = min(rect_right, anchor_max_x + 8)
peaks, properties = find_peaks(
    x_profile[peak_min_x:peak_max_x + 1],
    distance=12,
    prominence=30,
    height=50,
)
column_x = [int(p + peak_min_x) for p in peaks]
if len(column_x) != COL_COUNT:
    print(f"WARNING: expected {COL_COUNT} columns, found {len(column_x)} profile peaks")
    ranked = sorted(column_x, key=lambda x: x_profile[x], reverse=True)
    column_x = sorted(ranked[:COL_COUNT])
print(f"Columns: {column_x}")
print(f"Column gaps: {[column_x[i + 1] - column_x[i] for i in range(len(column_x) - 1)]}")

# Fit a small horizontal offset independently for each row. This handles the
# slight local misalignment without forcing every row onto one x-lattice.
predicted = []
for cy in row_y:
    row_anchors = [(b[0], b[1]) for b in blobs if abs(b[1] - cy) <= 10]
    residuals = []
    for bx, _ in row_anchors:
        nearest = min(column_x, key=lambda x: abs(x - bx))
        if abs(nearest - bx) <= 12:
            residuals.append(bx - nearest)
    offset = int(round(float(np.median(residuals)))) if residuals else 0
    row_columns = [x + offset for x in column_x]
    if len(row_anchors) >= 2:
        anchor_x = np.array([p[0] for p in row_anchors], dtype=float)
        anchor_y = np.array([p[1] for p in row_anchors], dtype=float)
        y_slope, y_intercept = np.polyfit(anchor_x, anchor_y, 1)
    else:
        y_slope, y_intercept = 0.0, float(cy)
    predicted.extend(
        (x, int(round(y_intercept + y_slope * x)))
        for x in row_columns
    )
    print(f"  row y={cy}: anchors={len(row_anchors)} x_offset={offset} y_slope={y_slope * 1000:.1f}/1000px")

modeled = predicted
predicted = []
refine_radius = max(6, round(6 * max(1.0, W / 1920)))
for px, py in modeled:
    x0 = max(0, px - refine_radius)
    x1 = min(W, px + refine_radius + 1)
    y0 = max(0, py - refine_radius)
    y1 = min(H, py + refine_radius + 1)

    x_local = darkness[max(0, py - refine_radius):min(H, py + refine_radius + 1), x0:x1].sum(axis=0)
    x_local = cv2.GaussianBlur(x_local.reshape(1, -1), (0, 0), max(1, refine_radius / 3)).ravel()
    refined_x = x0 + int(np.argmax(x_local))

    y_local = darkness[y0:y1, max(0, refined_x - refine_radius):min(W, refined_x + refine_radius + 1)].sum(axis=1)
    y_local = cv2.GaussianBlur(y_local.reshape(-1, 1), (0, 0), max(1, refine_radius / 3)).ravel()
    refined_y = y0 + int(np.argmax(y_local))
    predicted.append((refined_x, refined_y))

print(f"Center refinement: median shift={np.median([math.hypot(a - b, c - d) for (a, c), (b, d) in zip(predicted, modeled)]):.1f}px")
print(f"Predicted positions: {len(predicted)} ({COL_COUNT} columns x {ROW_COUNT} rows)")

with open("predicted_positions.json", "w") as f:
    json.dump({
        "rectangle": [rect_left, rect_top, rect_right, rect_bot],
        "positions": [[int(x), int(y)] for x, y in predicted],
        "rows": row_y,
        "columns": column_x,
    }, f, indent=2)
print("Saved: predicted_positions.json")

# Overlay only centers on the plain blot screenshot.
img_out = img.copy()
for x, y in predicted:
    cv2.circle(img_out, (x, y), 5, (0, 255, 0), 2)
for x, y, area in blobs:
    cv2.circle(img_out, (x, y), 9, (0, 0, 255), 2)
    cv2.drawMarker(img_out, (x, y), (0, 255, 255), cv2.MARKER_CROSS, 12, 2)
out_path = "/Users/admin/opencode-imagestudio/screenshots/detected_overlay.png"
cv2.imwrite(out_path, img_out)
print(f"\nSaved: {out_path}")
