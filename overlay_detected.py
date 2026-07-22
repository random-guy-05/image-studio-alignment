"""Create a visualization: original screenshot with detected data dots overlaid
as filled red circles, so the user can see exactly what was detected and what
was missed."""
import cv2, numpy as np

img = cv2.imread("/tmp/dots.png")
H, W = img.shape[:2]
print(f"Image: {W}x{H}")
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

# Find the blue rectangle (corner-based detection)
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
from collections import defaultdict
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
print(f"Rectangle: x=[{rect_left},{rect_right}]  y=[{rect_top},{rect_bot}]")

# Detect data dots with V<215
data_mask = cv2.inRange(hsv, np.array((0, 0, 0)), np.array((180, 50, 215)))
data_mask[:rect_top, :] = 0
data_mask[rect_bot:, :] = 0
data_mask[:, :rect_left] = 0
data_mask[:, rect_right:] = 0
blurred = cv2.GaussianBlur(data_mask, (5, 5), 1)
circles = cv2.HoughCircles(blurred, cv2.HOUGH_GRADIENT, dp=1, minDist=15,
                            param1=80, param2=15, minRadius=3, maxRadius=15)
dots = [] if circles is None else [(int(x), int(y), int(r)) for x, y, r in circles[0]]
print(f"Data dots detected: {len(dots)}")

# Draw the rectangle in green
cv2.rectangle(img, (rect_left, rect_top), (rect_right, rect_bot), (0, 255, 0), 2)

# Draw each detected dot as a filled red circle
for x, y, r in dots:
    cv2.circle(img, (x, y), 8, (0, 0, 255), -1)  # filled red, radius 8
    cv2.circle(img, (x, y), 8, (255, 255, 255), 1)  # white outline for visibility

# Add text label
cv2.putText(img, f"Detected: {len(dots)} data dots (V<215)", (rect_left, rect_top - 10),
            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

out_path = "/Users/admin/opencode-imagestudio/screenshots/detected_overlay.png"
cv2.imwrite(out_path, img)
print(f"Saved: {out_path}")
print(f"Open it to see what was detected (red) vs what was missed (no red)")
