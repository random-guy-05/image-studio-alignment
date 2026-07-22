"""Try tighter radius bounds to filter false positives."""
import cv2, numpy as np

cap = cv2.imread("/tmp/imagestudio.png")
hsv = cv2.cvtColor(cap, cv2.COLOR_BGR2HSV)

blue_mask = cv2.inRange(hsv, np.array((100, 120, 100)), np.array((130, 255, 255)))
grey_light = cv2.inRange(hsv, np.array((0, 0, 100)), np.array((180, 30, 200)))
grey_dark  = cv2.inRange(hsv, np.array((0, 0, 60)),  np.array((180, 60, 130)))
grey_mask  = cv2.bitwise_or(grey_light, grey_dark)

def hough(mask, p2, min_r, max_r):
    blurred = cv2.GaussianBlur(mask, (5, 5), 1)
    c = cv2.HoughCircles(blurred, cv2.HOUGH_GRADIENT, dp=1, minDist=20,
                         param1=80, param2=p2, minRadius=min_r, maxRadius=max_r)
    return [] if c is None else [(int(x), int(y), int(r)) for x, y, r in c[0]]

# Test combinations
print("BLUE:")
for r_min, r_max, p2 in [(10, 20, 15), (12, 20, 15), (12, 18, 15), (10, 18, 15), (8, 18, 15)]:
    cs = hough(blue_mask, p2, r_min, r_max)
    radii = [c[2] for c in cs]
    print(f"  r={r_min}-{r_max} p2={p2}: {len(cs)} circles  radii range [{min(radii) if radii else 0}, {max(radii) if radii else 0}]")

print("GREY:")
for r_min, r_max, p2 in [(10, 20, 20), (12, 20, 20), (12, 18, 20), (10, 18, 20), (8, 18, 20)]:
    cs = hough(grey_mask, p2, r_min, r_max)
    radii = [c[2] for c in cs]
    print(f"  r={r_min}-{r_max} p2={p2}: {len(cs)} circles  radii range [{min(radii) if radii else 0}, {max(radii) if radii else 0}]")
