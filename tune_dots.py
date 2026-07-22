"""Check the new screenshot: rectangle + data dot count with different params."""
import cv2, numpy as np
img = cv2.imread("/tmp/dots.png")
H, W = img.shape[:2]
print(f"Image: {W}x{H}")
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
blue_mask = cv2.inRange(hsv, np.array((100, 120, 100)), np.array((130, 255, 255)))

# Corner-based rectangle detection
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
if int((corners > 0).sum()) == 0:
    print("No corners found!"); exit()
ys, xs = np.where(corners > 0)
rect_left, rect_right = int(xs.min()), int(xs.max())
rect_top, rect_bot = int(ys.min()), int(ys.max())
print(f"Rectangle: x=[{rect_left},{rect_right}]  y=[{rect_top},{rect_bot}]  ({rect_right-rect_left}x{rect_bot-rect_top})")

# Data dot detection with different params
data_mask = cv2.inRange(hsv, np.array((0, 0, 0)), np.array((180, 50, 200)))
data_mask[:rect_top, :] = 0; data_mask[rect_bot:, :] = 0
data_mask[:, :rect_left] = 0; data_mask[:, rect_right:] = 0
blurred = cv2.GaussianBlur(data_mask, (5, 5), 1)

print(f"\nHoughCircles count with different params:")
for p2 in [10, 12, 15, 18, 20, 25, 30]:
    for minDist in [15, 20, 25]:
        c = cv2.HoughCircles(blurred, cv2.HOUGH_GRADIENT, dp=1, minDist=minDist,
                              param1=80, param2=p2, minRadius=3, maxRadius=15)
        n = 0 if c is None else len(c[0])
        print(f"  p2={p2:2d}  minDist={minDist}: {n}")
