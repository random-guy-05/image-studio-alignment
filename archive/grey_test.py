"""Test different grey ranges with HoughCircles to find the right params."""
import cv2
import numpy as np

cap = cv2.imread("/tmp/imagestudio.png")
hsv = cv2.cvtColor(cap, cv2.COLOR_BGR2HSV)

def hough_for_range(lo, hi, label):
    mask = cv2.inRange(hsv, np.array(lo), np.array(hi))
    blurred = cv2.GaussianBlur(mask, (5, 5), 1)
    circles = cv2.HoughCircles(
        blurred, cv2.HOUGH_GRADIENT,
        dp=1, minDist=20,
        param1=80, param2=15,
        minRadius=5, maxRadius=20
    )
    n = 0
    if circles is not None:
        n = len(circles[0])
    print(f"{label}: HSV{lo}->{hi}  mask_nonzero={int((mask>0).sum())}  hough_circles={n}")

# Try a range of grey options
hough_for_range((0, 0, 100), (180, 30, 200), "grey_v100-200")
hough_for_range((0, 0, 120), (180, 25, 180), "grey_v120-180")
hough_for_range((0, 0, 80),  (180, 40, 160), "grey_v80-160")
hough_for_range((0, 0, 100), (180, 20, 170), "grey_v100-170_s20")
hough_for_range((0, 0, 60),  (180, 50, 140), "grey_v60-140_s50")
hough_for_range((0, 0, 40),  (180, 60, 120), "dark_grey_v40-120_s60")

# Also test blue with the same hough params for reference
mask_b = cv2.inRange(hsv, np.array((100, 120, 100)), np.array((130, 255, 255)))
blurred_b = cv2.GaussianBlur(mask_b, (5, 5), 1)
c_b = cv2.HoughCircles(blurred_b, cv2.HOUGH_GRADIENT, dp=1, minDist=20, param1=80, param2=15, minRadius=5, maxRadius=20)
print(f"BLUE ref (same params): {0 if c_b is None else len(c_b[0])}")

# Try stricter param2 (higher = fewer circles)
mask_g = cv2.inRange(hsv, np.array((0, 0, 100)), np.array((180, 30, 200)))
blurred_g = cv2.GaussianBlur(mask_g, (5, 5), 1)
for p2 in [20, 25, 30, 40]:
    c = cv2.HoughCircles(blurred_g, cv2.HOUGH_GRADIENT, dp=1, minDist=20, param1=80, param2=p2, minRadius=5, maxRadius=20)
    n = 0 if c is None else len(c[0])
    print(f"  grey_v100-200 param2={p2}: {n}")
