"""Test the corner-based rectangle detection on the current screenshot."""
import cv2, numpy as np
img = cv2.imread("/tmp/dots.png")
H, W = img.shape[:2]
print(f"Image: {W}x{H}")
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
blue_mask = cv2.inRange(hsv, np.array((100, 120, 100)), np.array((130, 255, 255)))

# Build a mask of pixels that are part of LONG horizontal runs (>200px)
h_mask = np.zeros_like(blue_mask)
for y in range(H):
    row = blue_mask[y] > 0
    if not row.any(): continue
    padded = np.concatenate(([False], row, [False]))
    diffs = np.diff(padded.astype(int))
    starts = np.where(diffs == 1)[0]
    ends = np.where(diffs == -1)[0]
    for s, e in zip(starts, ends):
        if e - s > 200:
            h_mask[y, s:e] = 255

# Build a mask of pixels that are part of LONG vertical runs (>100px)
v_mask = np.zeros_like(blue_mask)
for x in range(W):
    col = blue_mask[:, x] > 0
    if not col.any(): continue
    padded = np.concatenate(([False], col, [False]))
    diffs = np.diff(padded.astype(int))
    starts = np.where(diffs == 1)[0]
    ends = np.where(diffs == -1)[0]
    for s, e in zip(starts, ends):
        if e - s > 100:
            v_mask[s:e, x] = 255

# Corners = intersection (pixels that are part of BOTH a long h-run AND a long v-run)
corners = cv2.bitwise_and(h_mask, v_mask)
corner_pixels = int((corners > 0).sum())
print(f"Corner pixels (h-run AND v-run): {corner_pixels}")

if corner_pixels > 0:
    ys, xs = np.where(corners > 0)
    # The corners form 4 clusters. Find them by clustering.
    # Simple approach: the bounding box of all corner pixels IS the rectangle.
    rect_left = int(xs.min())
    rect_right = int(xs.max())
    rect_top = int(ys.min())
    rect_bot = int(ys.max())
    print(f"Rectangle: x=[{rect_left},{rect_right}]  y=[{rect_top},{rect_bot}]")
    print(f"  width={rect_right-rect_left}  height={rect_bot-rect_top}")
    # Show corner clusters
    from collections import Counter
    y_bins = Counter((y // 10) * 10 for y in ys)
    x_bins = Counter((x // 10) * 10 for x in xs)
    print(f"  Y clusters: {sorted(y_bins.items())}")
    print(f"  X clusters: {sorted(x_bins.items())}")
else:
    print("No corners found!")
