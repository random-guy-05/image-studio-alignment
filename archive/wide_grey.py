"""Maximum-permissiveness grey detection — find every possible spot."""
import cv2, numpy as np

cap = cv2.imread("/tmp/imagestudio.png")
hsv = cv2.cvtColor(cap, cv2.COLOR_BGR2HSV)

# Very wide grey range
mask_wide = cv2.inRange(hsv, np.array((0, 0, 50)), np.array((180, 80, 230)))

# Also try: detect by the *ring* — many graphs have circles with a specific stroke
# Try edge-based detection: edges that are roughly circular

# And: detect any circular shape regardless of color
gray = cv2.cvtColor(cap, cv2.COLOR_BGR2GRAY)
gray_blurred = cv2.GaussianBlur(gray, (5, 5), 1)

# Use Hough on grayscale (finds any circle)
print("Hough on grayscale (any circle):")
for p2 in [15, 20, 25, 30]:
    c = cv2.HoughCircles(gray_blurred, cv2.HOUGH_GRADIENT, dp=1, minDist=20,
                         param1=80, param2=p2, minRadius=10, maxRadius=18)
    n = 0 if c is None else len(c[0])
    print(f"  p2={p2}: {n}")

# Try with very wide grey + low Hough threshold
print("\nWide grey mask:")
for p2 in [12, 15, 18, 20]:
    blurred = cv2.GaussianBlur(mask_wide, (5, 5), 1)
    c = cv2.HoughCircles(blurred, cv2.HOUGH_GRADIENT, dp=1, minDist=15,
                         param1=60, param2=p2, minRadius=6, maxRadius=20)
    n = 0 if c is None else len(c[0])
    print(f"  p2={p2}: {n}")

# Try Canny edges + Hough
print("\nCanny + Hough:")
edges = cv2.Canny(gray, 50, 150)
for p2 in [20, 25, 30, 35, 40]:
    c = cv2.HoughCircles(edges, cv2.HOUGH_GRADIENT, dp=1, minDist=20,
                         param1=50, param2=p2, minRadius=8, maxRadius=20)
    n = 0 if c is None else len(c[0])
    print(f"  p2={p2}: {n}")
