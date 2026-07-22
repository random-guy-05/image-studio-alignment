"""Analyze the aligned screenshot: detect blue circles and data dots,
measure the offset for each pair, and report misalignments."""
import cv2, numpy as np
import math

img = cv2.imread("/Users/admin/opencode-imagestudio/screenshots/aligned.png")
H, W = img.shape[:2]
print(f"Image: {W}x{H}")
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

# Detect blue circles
blue_mask = cv2.inRange(hsv, np.array((100, 120, 100)), np.array((130, 255, 255)))
bb = cv2.GaussianBlur(blue_mask, (5, 5), 1)
b_circles = cv2.HoughCircles(bb, cv2.HOUGH_GRADIENT, dp=1, minDist=15, param1=80, param2=30,
                              minRadius=6, maxRadius=18)
blues = [] if b_circles is None else [(int(x), int(y), int(r)) for x, y, r in b_circles[0]]
print(f"Blue circles: {len(blues)}")

# Detect data dots (black + grey + light grey)
data_mask = cv2.inRange(hsv, np.array((0, 0, 0)), np.array((180, 50, 220)))
db = cv2.GaussianBlur(data_mask, (5, 5), 1)
d_circles = cv2.HoughCircles(db, cv2.HOUGH_GRADIENT, dp=1, minDist=15, param1=80, param2=15,
                              minRadius=3, maxRadius=15)
dots = [] if d_circles is None else [(int(x), int(y), int(r)) for x, y, r in d_circles[0]]
print(f"Data dots: {len(dots)}")

# For each blue circle, find the nearest data dot and measure the offset
print(f"\nMisalignment analysis (blue center → nearest data dot):")
aligned = 0
misaligned = 0
no_dot = 0
offsets = []
for bx, by, br in blues:
    nearest = None
    nd = float("inf")
    for dx, dy, dr in dots:
        d = math.hypot(bx - dx, by - dy)
        if d < nd:
            nd = d
            nearest = (dx, dy)
    if nearest is None:
        no_dot += 1
        continue
    offset = nd
    offsets.append(offset)
    if offset < 10:
        aligned += 1
    else:
        misaligned += 1

print(f"  Aligned (offset < 10px): {aligned}")
print(f"  Misaligned (offset >= 10px): {misaligned}")
print(f"  No nearby dot: {no_dot}")
if offsets:
    print(f"  Offset stats: min={min(offsets):.1f}  max={max(offsets):.1f}  avg={sum(offsets)/len(offsets):.1f}")
    # Distribution
    for t in [5, 10, 15, 20, 30, 50, 100]:
        n = sum(1 for o in offsets if o > t)
        print(f"    offset > {t}px: {n}")

# Show the worst 10 misalignments
print(f"\nWorst 10 misalignments:")
worst = sorted(zip(blues, offsets), key=lambda x: -x[1])[:10]
for (bx, by, br), off in worst:
    # Find the nearest dot for this blue
    nearest = min(dots, key=lambda d: math.hypot(bx-d[0], by-d[1]))
    dx, dy = nearest[0], nearest[1]
    print(f"  blue ({bx},{by}) → dot ({dx},{dy})  offset={off:.1f}px  dx={dx-bx}  dy={dy-by}")
