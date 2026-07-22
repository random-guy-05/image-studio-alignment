"""Find the right grey combination."""
import cv2, numpy as np

cap = cv2.imread("/tmp/imagestudio.png")
hsv = cv2.cvtColor(cap, cv2.COLOR_BGR2HSV)

# Try combining dark + light grey
mask_light = cv2.inRange(hsv, np.array((0, 0, 100)), np.array((180, 30, 200)))
mask_dark = cv2.inRange(hsv, np.array((0, 0, 60)), np.array((180, 60, 130)))
mask_combined = cv2.bitwise_or(mask_light, mask_dark)

def hough(mask, p2, label):
    blurred = cv2.GaussianBlur(mask, (5, 5), 1)
    c = cv2.HoughCircles(blurred, cv2.HOUGH_GRADIENT, dp=1, minDist=20,
                         param1=80, param2=p2, minRadius=5, maxRadius=20)
    n = 0 if c is None else len(c[0])
    print(f"{label}: {n}")

for p2 in [15, 18, 20, 22, 25]:
    hough(mask_light, p2, f"light_only p2={p2}")
print("---")
for p2 in [15, 18, 20, 22, 25]:
    hough(mask_combined, p2, f"light+dark p2={p2}")
print("---")
# Also try: mask out the bright/white background by excluding V>200
mask_no_white = cv2.inRange(hsv, np.array((0, 0, 60)), np.array((180, 50, 180)))
for p2 in [15, 18, 20, 22]:
    hough(mask_no_white, p2, f"no_white (v60-180) p2={p2}")
