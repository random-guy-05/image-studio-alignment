"""Find ALL data dots in the aligned screenshot, including the really light ones."""
import cv2, numpy as np
import math

img = cv2.imread("/Users/admin/opencode-imagestudio/screenshots/aligned.png")
H, W = img.shape[:2]
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

# Try different V thresholds
print("Data dot detection with different V thresholds:")
for v_max in [180, 200, 210, 215, 220, 225, 230, 235, 240]:
    mask = cv2.inRange(hsv, np.array((0, 0, 0)), np.array((180, 50, v_max)))
    blurred = cv2.GaussianBlur(mask, (5, 5), 1)
    circles = cv2.HoughCircles(blurred, cv2.HOUGH_GRADIENT, dp=1, minDist=15,
                                param1=80, param2=15, minRadius=3, maxRadius=15)
    n = 0 if circles is None else len(circles[0])
    print(f"  V<{v_max}: {n} dots")

# Also check: what's the V value at known dot positions?
# Sample a few dots detected at V<200 and check their actual V
mask200 = cv2.inRange(hsv, np.array((0, 0, 0)), np.array((180, 50, 200)))
blurred200 = cv2.GaussianBlur(mask200, (5, 5), 1)
circles200 = cv2.HoughCircles(blurred200, cv2.HOUGH_GRADIENT, dp=1, minDist=15,
                               param1=80, param2=15, minRadius=3, maxRadius=15)
if circles200 is not None:
    print(f"\nSample V values at detected dots (V<200):")
    for x, y, r in circles200[0][:10]:
        x, y = int(x), int(y)
        h, s, v = hsv[y, x]
        print(f"  ({x},{y}): HSV=({h},{s},{v})")

# Now look for dots that are ONLY visible at higher V thresholds
# (detected at V<230 but NOT at V<200)
mask230 = cv2.inRange(hsv, np.array((0, 0, 0)), np.array((180, 50, 230)))
blurred230 = cv2.GaussianBlur(mask230, (5, 5), 1)
circles230 = cv2.HoughCircles(blurred230, cv2.HOUGH_GRADIENT, dp=1, minDist=15,
                               param1=80, param2=15, minRadius=3, maxRadius=15)
if circles230 is not None:
    dots200 = set((int(x//5), int(y//5)) for x, y, r in circles200[0]) if circles200 is not None else set()
    new_dots = []
    for x, y, r in circles230[0]:
        key = (int(x//5), int(y//5))
        if key not in dots200:
            x, y = int(x), int(y)
            h, s, v = hsv[y, x]
            new_dots.append((x, y, v))
    print(f"\nDots found at V<230 but NOT at V<200: {len(new_dots)}")
    for x, y, v in sorted(new_dots, key=lambda d: d[2])[:15]:
        print(f"  ({x},{y}): V={v}")
