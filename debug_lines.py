import cv2, numpy as np
img = cv2.imread("/tmp/dots.png")
H, W = img.shape[:2]
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
blue_mask = cv2.inRange(hsv, np.array((100, 120, 100)), np.array((130, 255, 255)))
edges = cv2.Canny(blue_mask, 50, 150)
lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=50, minLineLength=200, maxLineGap=20)
print(f"lines type: {type(lines)}")
print(f"lines shape: {lines.shape if lines is not None else None}")
if lines is not None and len(lines) > 0:
    print(f"First line: {lines[0]}")
    print(f"First line type: {type(lines[0])}")
    if len(lines[0].shape) > 0:
        print(f"First line shape: {lines[0].shape}")
        print(f"First line flat: {lines[0].flatten()}")
