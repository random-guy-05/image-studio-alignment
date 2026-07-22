import cv2, numpy as np
img = cv2.imread("/tmp/dots.png")
H, W = img.shape[:2]
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
blue_mask = cv2.inRange(hsv, np.array((100, 120, 100)), np.array((130, 255, 255)))
edges = cv2.Canny(blue_mask, 50, 150)
lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=50, minLineLength=200, maxLineGap=20)
print(f"Found {len(lines)} lines:")
for line in lines:
    x1, y1, x2, y2 = line[0], line[1], line[2], line[3]
    is_horiz = abs(y2 - y1) < 10
    is_vert = abs(x2 - x1) < 10
    direction = "H" if is_horiz else ("V" if is_vert else "?")
    print(f"  {direction}: ({x1},{y1}) -> ({x2},{y2})  len={max(abs(x2-x1), abs(y2-y1))}")
