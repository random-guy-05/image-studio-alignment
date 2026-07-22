"""Try multiple detection strategies and pick the one that finds the most dots.
Then overlay ALL detected dots on the original screenshot."""
import cv2, numpy as np
import math

img = cv2.imread("/tmp/dots.png")
H, W = img.shape[:2]
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

# Find rectangle
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

# Strategy: try MANY combinations and find the one with the most dots
# that are INSIDE the rectangle
best_dots = []
best_count = 0
best_params = None

for v_max in [200, 210, 215, 220, 225, 230, 235, 240, 245, 250]:
    for s_max in [30, 50, 70, 100]:
        for p2 in [10, 12, 15, 18, 20]:
            for minDist in [10, 12, 15, 20]:
                mask = cv2.inRange(hsv, np.array((0, 0, 0)), np.array((180, s_max, v_max)))
                mask[:rect_top, :] = 0; mask[rect_bot:, :] = 0
                mask[:, :rect_left] = 0; mask[:, rect_right:] = 0
                blurred = cv2.GaussianBlur(mask, (5, 5), 1)
                circles = cv2.HoughCircles(blurred, cv2.HOUGH_GRADIENT, dp=1, minDist=minDist,
                                            param1=80, param2=p2, minRadius=2, maxRadius=15)
                if circles is None: continue
                dots = [(int(x), int(y)) for x, y, r in circles[0]
                        if rect_left < x < rect_right and rect_top < y < rect_bot]
                # Dedup
                deduped = []
                for d in dots:
                    if not any(math.hypot(d[0]-q[0], d[1]-q[1]) < 5 for q in deduped):
                        deduped.append(d)
                if len(deduped) > best_count and len(deduped) < 400:  # sanity cap
                    best_count = len(deduped)
                    best_dots = deduped
                    best_params = (v_max, s_max, p2, minDist)

print(f"\nBest params: V<{best_params[0]}  S<{best_params[1]}  p2={best_params[2]}  minDist={best_params[3]}")
print(f"Best count: {best_count} dots")

# Also try connected components as an alternative
print("\nTrying connected components:")
for v_max in [200, 215, 220, 230, 240, 250]:
    for s_max in [30, 50, 70]:
        mask = cv2.inRange(hsv, np.array((0, 0, 0)), np.array((180, s_max, v_max)))
        mask[:rect_top, :] = 0; mask[rect_bot:, :] = 0
        mask[:, :rect_left] = 0; mask[:, rect_right:] = 0
        num, labels, stats, cents = cv2.connectedComponentsWithStats(mask, 8)
        dots_cc = []
        for i in range(1, num):
            cx, cy = cents[i]
            area = stats[i][4]
            if not (rect_left < cx < rect_right and rect_top < cy < rect_bot): continue
            if area < 3 or area > 500: continue
            dots_cc.append((int(cx), int(cy)))
        # Dedup
        deduped = []
        for d in dots_cc:
            if not any(math.hypot(d[0]-q[0], d[1]-q[1]) < 5 for q in deduped):
                deduped.append(d)
        if len(deduped) > best_count and len(deduped) < 400:
            best_count = len(deduped)
            best_dots = deduped
            best_params = (f"CC V<{v_max} S<{s_max}",)
            print(f"  CC V<{v_max} S<{s_max}: {len(deduped)} dots (NEW BEST)")

print(f"\nFinal best: {best_count} dots with params {best_params}")

# Draw overlay
img_out = img.copy()
cv2.rectangle(img_out, (rect_left, rect_top), (rect_right, rect_bot), (0, 255, 0), 2)
for x, y in best_dots:
    cv2.circle(img_out, (x, y), 8, (0, 0, 255), -1)
    cv2.circle(img_out, (x, y), 8, (255, 255, 255), 1)
cv2.putText(img_out, f"Detected: {best_count} data dots", (rect_left, rect_top - 10),
            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
out_path = "/Users/admin/opencode-imagestudio/screenshots/detected_overlay.png"
cv2.imwrite(out_path, img_out)
print(f"\nSaved: {out_path}")
