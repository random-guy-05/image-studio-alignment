"""Detect the GRID structure of the data dots.
Cytokine arrays are printed in a regular grid. If we find the grid spacing,
we can predict every dot position and just check if a dot exists there.
This eliminates false positives (gaps) and finds faint dots (we look at
specific positions, not everywhere)."""
import json
import cv2, numpy as np
import math
from collections import Counter, defaultdict
import pyautogui
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
data_mask = cv2.inRange(hsv, np.array((0, 0, 0)), np.array((180, 50, 215)))
data_mask[:rect_top, :] = 0; data_mask[rect_bot:, :] = 0
data_mask[:, :rect_left] = 0; data_mask[:, rect_right:] = 0

# Hough parameters scale with the full-screen screenshot density.
screen_w, screen_h = pyautogui.size()
scale = (W / screen_w + H / screen_h) / 2
kernel = max(5, int(round(5 * scale)) | 1)
blurred = cv2.GaussianBlur(data_mask, (kernel, kernel), scale)
circles = cv2.HoughCircles(
    blurred,
    cv2.HOUGH_GRADIENT,
    dp=1,
    minDist=round(16.5 * scale),
    param1=80,
    param2=9,
    minRadius=round(3 * scale),
    maxRadius=round(15 * scale),
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

# Recover 24 x-columns from the entire rectangle. This does not assume one
# global spacing; larger gaps remain explicit subgrid gaps.
ROW_COUNT = 10
COL_COUNT = 24
darkness = np.clip(225 - hsv[:, :, 2].astype(float), 0, 225)
x_profile = darkness[rect_top:rect_bot, rect_left:rect_right].sum(axis=0)
x_profile = np.maximum(
    x_profile - cv2.GaussianBlur(x_profile.reshape(1, -1), (0, 0), 20 * scale).ravel(),
    0,
)
peaks, _ = find_peaks(
    x_profile,
    distance=max(12, round(12 * scale)),
    prominence=max(30, round(100 * scale * scale)),
    height=max(50, round(100 * scale * scale)),
)
column_x = [int(p + rect_left) for p in peaks]
if len(column_x) != COL_COUNT:
    raise RuntimeError(f"Expected {COL_COUNT} column peaks, found {len(column_x)}")
print(f"Columns: {column_x}")
print(f"Column gaps: {[column_x[i + 1] - column_x[i] for i in range(len(column_x) - 1)]}")

# Recover row centers from the learned columns. If one row is too faint to
# produce a profile peak, insert it at the largest unexplained vertical gap.
y_profile = np.zeros(rect_bot - rect_top, dtype=float)
for cx in column_x:
    x0, x1 = max(0, cx - round(10 * scale)), min(W, cx + round(10 * scale) + 1)
    y_profile += darkness[rect_top:rect_bot, x0:x1].sum(axis=1)
y_profile = np.maximum(
    y_profile - cv2.GaussianBlur(y_profile.reshape(-1, 1), (0, 0), 20 * scale).ravel(),
    0,
)
y_peaks, _ = find_peaks(
    y_profile,
    distance=max(20, round(15 * scale)),
    prominence=max(30, round(100 * scale * scale)),
    height=max(50, round(100 * scale * scale)),
)
row_y = [int(p + rect_top) for p in y_peaks]
while len(row_y) < ROW_COUNT:
    gaps = [(row_y[i + 1] - row_y[i], i) for i in range(len(row_y) - 1)]
    gap, index = max(gaps)
    row_y.insert(index + 1, int(round((row_y[index] + row_y[index + 1]) / 2)))
if len(row_y) > ROW_COUNT:
    row_y = sorted(row_y, key=lambda y: y_profile[y - rect_top], reverse=True)[:ROW_COUNT]
    row_y.sort()
print(f"Rows: {row_y}")
print(f"Row gaps: {[row_y[i + 1] - row_y[i] for i in range(len(row_y) - 1)]}")

# Fit a small horizontal offset independently for each row. This handles the
# slight local misalignment without forcing every row onto one x-lattice.
row_band = min(20, max(10, int(min(np.diff(row_y)) * 0.45)))
predicted = []
for cy in row_y:
    row_anchors = [(b[0], b[1]) for b in blobs if abs(b[1] - cy) <= row_band]
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
    fit_errors = []
    for bx, by in row_anchors:
        nearest_x = min(row_columns, key=lambda x: abs(x - bx))
        fit_errors.append(math.hypot(nearest_x - bx, y_intercept + y_slope * nearest_x - by))
    print(f"  row y={cy}: anchors={len(row_anchors)} x_offset={offset} "
          f"y_slope={y_slope * 1000:.1f}/1000px "
          f"fit_median={np.median(fit_errors) if fit_errors else 0:.1f}px")

modeled = predicted
predicted = []
refine_radius = max(8, round(6 * scale))
for px, py in modeled:
    x0 = max(0, px - refine_radius)
    x1 = min(W, px + refine_radius + 1)
    y0 = max(0, py - refine_radius)
    y1 = min(H, py + refine_radius + 1)

    x_profile = darkness[max(0, py - refine_radius):min(H, py + refine_radius + 1), x0:x1].sum(axis=0)
    x_profile = cv2.GaussianBlur(x_profile.reshape(1, -1), (0, 0), max(1, scale)).ravel()
    refined_x = x0 + int(np.argmax(x_profile))

    y_profile = darkness[y0:y1, max(0, refined_x - refine_radius):min(W, refined_x + refine_radius + 1)].sum(axis=1)
    y_profile = cv2.GaussianBlur(y_profile.reshape(-1, 1), (0, 0), max(1, scale)).ravel()
    refined_y = y0 + int(np.argmax(y_profile))
    predicted.append((refined_x, refined_y))

refinement_error = [math.hypot(a - b, c - d) for (a, c), (b, d) in zip(predicted, modeled)]
print(f"Center refinement: median shift={np.median(refinement_error):.1f}px max shift={max(refinement_error):.1f}px")
print(f"Predicted positions: {len(predicted)} ({COL_COUNT} columns x {ROW_COUNT} rows)")
anchor_errors = []
for bx, by, _ in blobs:
    anchor_errors.append(min(math.hypot(bx - px, by - py) for px, py in predicted))
print(f"Anchor-to-prediction error: median={np.median(anchor_errors):.1f}px max={max(anchor_errors):.1f}px")

with open("predicted_positions.json", "w") as f:
    json.dump({
        "rectangle": [rect_left, rect_top, rect_right, rect_bot],
        "positions": [[int(x), int(y)] for x, y in predicted],
        "rows": row_y,
        "columns": column_x,
    }, f, indent=2)
print("Saved: predicted_positions.json")

# Overlay only dot centers on the plain screenshot:
# green = predicted positions, red/yellow = discovered Hough centers.
img_out = img.copy()
for x, y in predicted:
    cv2.circle(img_out, (x, y), max(3, round(5 * scale)), (0, 255, 0), 2)
for x, y, area in blobs:
    cv2.circle(img_out, (x, y), max(4, round(8 * scale)), (0, 0, 255), 2)
    cv2.drawMarker(img_out, (x, y), (0, 255, 255), cv2.MARKER_CROSS, max(8, round(12 * scale)), 2)
out_path = "/Users/admin/opencode-imagestudio/screenshots/detected_overlay.png"
cv2.imwrite(out_path, img_out)
print(f"\nSaved: {out_path}")
