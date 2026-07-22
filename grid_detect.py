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

full_img = cv2.imread("screenshots/dots.png")
scale_x = 2.0 if full_img.shape[1] >= 2500 else 1.0
scale_y = 2.0 if full_img.shape[0] >= 1500 else 1.0
screen_w = round(full_img.shape[1] / scale_x)
screen_h = round(full_img.shape[0] / scale_y)
img = cv2.resize(full_img, (screen_w, screen_h), interpolation=cv2.INTER_AREA)
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
if rect_right - rect_left < 100 or rect_bot - rect_top < 100:
    full_hsv = cv2.cvtColor(full_img, cv2.COLOR_BGR2HSV)
    full_blue = cv2.inRange(full_hsv, np.array((100, 120, 100)), np.array((130, 255, 255)))
    full_h = np.zeros_like(full_blue)
    for y in range(full_blue.shape[0]):
        row = full_blue[y] > 0
        padded = np.concatenate(([False], row, [False]))
        diffs = np.diff(padded.astype(int))
        starts = np.where(diffs == 1)[0]; ends = np.where(diffs == -1)[0]
        for start, end in zip(starts, ends):
            if end - start > 200 * scale_x:
                full_h[y, start:end] = 255
    full_v = np.zeros_like(full_blue)
    for x in range(full_blue.shape[1]):
        col = full_blue[:, x] > 0
        padded = np.concatenate(([False], col, [False]))
        diffs = np.diff(padded.astype(int))
        starts = np.where(diffs == 1)[0]; ends = np.where(diffs == -1)[0]
        for start, end in zip(starts, ends):
            if end - start > 100 * scale_y:
                full_v[start:end, x] = 255
    full_ys, full_xs = np.where(cv2.bitwise_and(full_h, full_v) > 0)
    full_clusters = defaultdict(list)
    for y, x in zip(full_ys, full_xs):
        full_clusters[(y // round(20 * scale_y), x // round(20 * scale_x))].append((y, x))
    full_centers = [(sum(p[1] for p in points) / len(points), sum(p[0] for p in points) / len(points))
                    for points in full_clusters.values()]
    rect_left = round(min(c[0] for c in full_centers) / scale_x)
    rect_right = round(max(c[0] for c in full_centers) / scale_x)
    rect_top = round(min(c[1] for c in full_centers) / scale_y)
    rect_bot = round(max(c[1] for c in full_centers) / scale_y)
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

# Prompt user for grid dimensions before any detection,
# so parameters can scale to the image.
default_rows = 10
default_cols = 24
print(f"Grid layout (default {default_rows}x{default_cols}):")
try:
    ROW_COUNT = int(input(f"  Rows [{default_rows}]: ") or default_rows)
    COL_COUNT = int(input(f"  Cols [{default_cols}]: ") or default_cols)
except (EOFError, KeyboardInterrupt):
    ROW_COUNT = default_rows
    COL_COUNT = default_cols
print(f"Using {ROW_COUNT} rows x {COL_COUNT} columns\n")

# Estimate dot spacing from rectangle size; scales detection parameters.
rect_w = rect_right - rect_left
rect_h = rect_bot - rect_top
spacing_x = rect_w / max(COL_COUNT - 1, 1)
spacing_y = rect_h / max(ROW_COUNT - 1, 1)
est_spacing = (spacing_x + spacing_y) / 2

# Find blobs with HoughCircles (conservative: no false positives, FN acceptable)
blurred = cv2.GaussianBlur(data_mask, (5, 5), 1)
circles = cv2.HoughCircles(
    blurred,
    cv2.HOUGH_GRADIENT,
    dp=1,
    minDist=max(12, round(est_spacing * 0.6)),
    param1=80,
    param2=12,
    minRadius=max(2, round(est_spacing * 0.1)),
    maxRadius=max(10, round(est_spacing * 0.55)),
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
print(f"\n=== DATA DOTS DETECTED: {len(blobs)} ===\n")

# Fully black dots have a more reliable center in their connected pixel mass
# than in a circle fit. Only recenter compact black components; pale dots and
# large/ambiguous dark regions are left unchanged.
black_mask = cv2.inRange(hsv, np.array((0, 0, 0)), np.array((180, 50, 80)))
black_mask[:rect_top, :] = 0; black_mask[rect_bot:, :] = 0
black_mask[:, :rect_left] = 0; black_mask[:, rect_right:] = 0
black_count, black_labels, black_stats, black_centers = cv2.connectedComponentsWithStats(black_mask, 8)
black_components = []
for component in range(1, black_count):
    bx, by, bw, bh, area = black_stats[component]
    cx, cy = black_centers[component]
    if area >= 5 and bw <= 20 and bh <= 20:
        black_components.append((cx, cy, component, area))

black_refined = 0
refined_blobs = []
for cx, cy, area in blobs:
    candidates = [component for component in black_components
                  if math.hypot(component[0] - cx, component[1] - cy) <= 8]
    if candidates:
        bx, by, _, black_area = min(candidates, key=lambda component: math.hypot(component[0] - cx, component[1] - cy))
        refined_blobs.append((round(bx), round(by), max(area, black_area)))
        black_refined += 1
    else:
        refined_blobs.append((cx, cy, area))
blobs = refined_blobs
print(f"\n=== BLACK-BLOB CENTER CORRECTIONS: {black_refined} ===\n")

darkness = np.clip(225 - hsv[:, :, 2].astype(float), 0, 225)
x_profile = darkness[rect_top:rect_bot, rect_left:rect_right].sum(axis=0)
x_blur = max(6, round(spacing_x * 0.35))
x_profile = np.maximum(x_profile - cv2.GaussianBlur(x_profile.reshape(1, -1), (0, 0), x_blur).ravel(), 0)
x_distance = max(8, round(spacing_x * 0.4))
x_prom = max(30, round(spacing_x * 2.5))
peaks, _ = find_peaks(x_profile, distance=x_distance, prominence=x_prom, height=x_prom)
column_x = [int(p + rect_left) for p in peaks]
if len(column_x) > COL_COUNT:
    anchor_max_x = max(b[0] for b in blobs)
    column_x = [x for x in column_x if x <= anchor_max_x + 12]
if len(column_x) > COL_COUNT:
    column_x = sorted(column_x, key=lambda x: x_profile[x - rect_left], reverse=True)[:COL_COUNT]
    column_x.sort()
if len(column_x) < COL_COUNT:
    raise RuntimeError(f"Expected {COL_COUNT} column peaks, found only {len(column_x)}")
print(f"Columns: {column_x}")
print(f"Column gaps: {[column_x[i + 1] - column_x[i] for i in range(len(column_x) - 1)]}")

y_profile = np.zeros(rect_bot - rect_top, dtype=float)
y_window = max(3, round(spacing_x * 0.2))
for cx in column_x:
    y_profile += darkness[rect_top:rect_bot, max(0, cx - y_window):min(W, cx + y_window + 1)].sum(axis=1)
y_blur = max(6, round(spacing_y * 0.35))
y_profile = np.maximum(y_profile - cv2.GaussianBlur(y_profile.reshape(-1, 1), (0, 0), y_blur).ravel(), 0)
y_distance = max(10, round(spacing_y * 0.65))
y_prom = max(30, round(spacing_y * 2.5))
y_peaks, _ = find_peaks(y_profile, distance=y_distance, prominence=y_prom, height=y_prom)
row_y = [int(p + rect_top) for p in y_peaks]
while len(row_y) < ROW_COUNT:
    gaps = [(row_y[i + 1] - row_y[i], i) for i in range(len(row_y) - 1)]
    gap_size, index = max(gaps)
    margin = max(1, round(spacing_y * 0.2))
    y_start = row_y[index] + margin
    y_end = row_y[index + 1] - margin
    if y_end > y_start and y_start >= rect_top:
        best_y = y_start + int(np.argmax(y_profile[y_start - rect_top:y_end - rect_top]))
    else:
        best_y = round((row_y[index] + row_y[index + 1]) / 2)
    row_y.insert(index + 1, best_y)
if len(row_y) > ROW_COUNT:
    row_y = sorted(row_y, key=lambda y: y_profile[y - rect_top], reverse=True)[:ROW_COUNT]
    row_y.sort()
print(f"\nRows: {row_y}")
print(f"Row gaps: {[row_y[i + 1] - row_y[i] for i in range(len(row_y) - 1)]}")

def fit_grid(anchors):
    stable_slopes = []
    for cy in row_y:
        row_anchors = [(b[0], b[1]) for b in anchors if abs(b[1] - cy) <= 10]
        if len(row_anchors) >= 5:
            anchor_x = np.array([p[0] for p in row_anchors], dtype=float)
            anchor_y = np.array([p[1] for p in row_anchors], dtype=float)
            stable_slopes.append(np.polyfit(anchor_x, anchor_y, 1)[0])
    default_slope = float(np.median(stable_slopes)) if stable_slopes else 0.0

    positions = []
    for cy in row_y:
        row_anchors = [(b[0], b[1]) for b in anchors if abs(b[1] - cy) <= 10]
        residuals = []
        for bx, _ in row_anchors:
            nearest = min(column_x, key=lambda x: abs(x - bx))
            if abs(nearest - bx) <= 12:
                residuals.append(bx - nearest)
        offset = int(round(float(np.median(residuals)))) if residuals else 0
        row_columns = [x + offset for x in column_x]
        if len(row_anchors) >= 5:
            anchor_x = np.array([p[0] for p in row_anchors], dtype=float)
            anchor_y = np.array([p[1] for p in row_anchors], dtype=float)
            y_slope, y_intercept = np.polyfit(anchor_x, anchor_y, 1)
        else:
            y_slope = default_slope
            y_intercept = float(cy) - y_slope * float(np.median(row_columns))
        positions.extend(
            (x, int(round(y_intercept + y_slope * x)))
            for x in row_columns
        )
        print(f"  row y={cy}: anchors={len(row_anchors)} x_offset={offset} y_slope={y_slope * 1000:.1f}/1000px")
    return positions


# Reject Hough candidates that do not land near the first structural model.
# This keeps the overlay and refit anchor set false-positive conservative.
initial_model = fit_grid(blobs)
anchor_distances = np.array([
    min(math.hypot(b[0] - x, b[1] - y) for x, y in initial_model)
    for b in blobs
])
distance_median = float(np.median(anchor_distances))
distance_mad = float(np.median(np.abs(anchor_distances - distance_median)))
robust_sigma = max(0.5, 1.4826 * distance_mad)
anchor_cutoff = max(6.0, distance_median + 3.0 * robust_sigma)
blobs = [b for b, distance in zip(blobs, anchor_distances) if distance <= anchor_cutoff]
print(f"Anchor residuals: median={distance_median:.1f}px MAD={distance_mad:.1f}px cutoff={anchor_cutoff:.1f}px")
print(f"Certain anchors after structural filter: {len(blobs)} (removed {len(anchor_distances) - len(blobs)})")
predicted = fit_grid(blobs)

modeled = predicted
predicted = list(modeled)

# Correct only from retained Hough centers. A dark-pixel search is not allowed
# to move a prediction onto an unrelated nearby blot or artifact.
candidate_matches = sorted(
    (
        math.hypot(px - bx, py - by),
        position_index,
        anchor_index,
    )
    for position_index, (px, py) in enumerate(modeled)
    for anchor_index, (bx, by, _) in enumerate(blobs)
    if math.hypot(px - bx, py - by) <= anchor_cutoff
)
used_positions = set()
used_anchors = set()
for distance, position_index, anchor_index in candidate_matches:
    if position_index in used_positions or anchor_index in used_anchors:
        continue
    bx, by, _ = blobs[anchor_index]
    predicted[position_index] = (bx, by)
    used_positions.add(position_index)
    used_anchors.add(anchor_index)

# Refine only model-only positions when the local blot is strong enough to be
# trusted. Pale positions remain exactly at the Hough-derived model center.
refine_radius = max(8, round(est_spacing * 0.3))
anchor_strengths = []
for bx, by, _ in blobs:
    patch = darkness[max(0, by - refine_radius):min(H, by + refine_radius + 1),
                     max(0, bx - refine_radius):min(W, bx + refine_radius + 1)]
    anchor_strengths.append(float(patch.max()))
refine_cutoff = float(np.percentile(anchor_strengths, 30)) if anchor_strengths else float("inf")
refined_positions = 0
for position_index, (px, py) in enumerate(predicted):
    if position_index in used_positions:
        continue
    x0 = max(0, px - refine_radius)
    x1 = min(W, px + refine_radius + 1)
    y0 = max(0, py - refine_radius)
    y1 = min(H, py + refine_radius + 1)
    patch = darkness[y0:y1, x0:x1]
    peak_strength = float(patch.max())
    if peak_strength < refine_cutoff:
        continue
    x_local = patch.sum(axis=0)
    x_local = cv2.GaussianBlur(x_local.reshape(1, -1), (0, 0), max(1, refine_radius / 3)).ravel()
    refined_x = x0 + int(np.argmax(x_local))
    y_local = patch[:, max(0, refined_x - x0 - refine_radius):min(patch.shape[1], refined_x - x0 + refine_radius + 1)].sum(axis=1)
    y_local = cv2.GaussianBlur(y_local.reshape(-1, 1), (0, 0), max(1, refine_radius / 3)).ravel()
    refined_y = y0 + int(np.argmax(y_local))
    predicted[position_index] = (refined_x, refined_y)
    refined_positions += 1

print(f"Hough-anchored centers: {len(used_positions)}; model-only centers: {len(predicted) - len(used_positions)}")
print(f"Conditional center refinement: {refined_positions} positions; confidence cutoff={refine_cutoff:.1f}")
print(f"Predicted positions: {len(predicted)} ({COL_COUNT} columns x {ROW_COUNT} rows)")

with open("predicted_positions.json", "w") as f:
    json.dump({
        "rectangle": [rect_left, rect_top, rect_right, rect_bot],
        "positions": [[int(x), int(y)] for x, y in predicted],
        "rows": row_y,
        "columns": column_x,
        "image_size": [int(full_img.shape[1]), int(full_img.shape[0])],
        "scale": [scale_x, scale_y],
    }, f, indent=2)
print("Saved: predicted_positions.json")

# Overlay only centers on the plain blot screenshot.
img_out = full_img.copy()
for x, y in predicted:
    cv2.circle(img_out, (round(x * scale_x), round(y * scale_y)), round(5 * scale_x), (0, 255, 0), 2)
for x, y, area in blobs:
    center = (round(x * scale_x), round(y * scale_y))
    cv2.circle(img_out, center, round(9 * scale_x), (0, 0, 255), 2)
    cv2.drawMarker(img_out, center, (0, 255, 255), cv2.MARKER_CROSS, round(12 * scale_x), 2)
out_path = "screenshots/detected_overlay.png"
cv2.imwrite(out_path, img_out)
print(f"\nSaved: {out_path}")
