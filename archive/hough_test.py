"""Test HoughCircles detection on the same image."""
import cv2
import numpy as np

cap = cv2.imread("/tmp/imagestudio.png")
hsv = cv2.cvtColor(cap, cv2.COLOR_BGR2HSV)

# Blue ring outlines
blue_mask = cv2.inRange(hsv, np.array((100, 120, 100)), np.array((130, 255, 255)))
# Grey spots
grey_mask = cv2.inRange(hsv, np.array((0, 0, 60)), np.array((180, 40, 200)))

# Show some stats on the masks
print("blue_mask nonzero:", int((blue_mask > 0).sum()))
print("grey_mask nonzero:", int((grey_mask > 0).sum()))

# Show size distribution of blue connected components
n, labels, stats, _ = cv2.connectedComponentsWithStats(blue_mask, 8)
sizes = sorted([stats[i][4] for i in range(1, n)], reverse=True)
print(f"blue components: {n-1}, top 20 areas: {sizes[:20]}")
print(f"blue components with area 10-1000: {sum(1 for s in sizes if 10 <= s <= 1000)}")
print(f"blue components with area 100-3000: {sum(1 for s in sizes if 100 <= s <= 3000)}")

# HoughCircles on blue mask
blue_gray = blue_mask
# Reduce noise
blue_gray = cv2.GaussianBlur(blue_gray, (5, 5), 1)
circles = cv2.HoughCircles(
    blue_gray, cv2.HOUGH_GRADIENT,
    dp=1, minDist=15,
    param1=80, param2=12,
    minRadius=4, maxRadius=20
)
if circles is not None:
    circles = np.uint16(np.around(circles[0]))
    print(f"BLUE HoughCircles found: {len(circles)}")
    print(f"  first 5: {circles[:5].tolist()}")
    print(f"  radius range: [{circles[:,2].min()}, {circles[:,2].max()}]")
else:
    print("BLUE HoughCircles found: 0")

# HoughCircles on grey mask
grey_gray = cv2.GaussianBlur(grey_mask, (5, 5), 1)
g_circles = cv2.HoughCircles(
    grey_gray, cv2.HOUGH_GRADIENT,
    dp=1, minDist=15,
    param1=80, param2=12,
    minRadius=4, maxRadius=20
)
if g_circles is not None:
    g_circles = np.uint16(np.around(g_circles[0]))
    print(f"GREY HoughCircles found: {len(g_circles)}")
    print(f"  first 5: {g_circles[:5].tolist()}")
else:
    print("GREY HoughCircles found: 0")
