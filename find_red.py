"""Look for a RED rectangle in the screenshot (the user says the actual dots are inside it)."""
import cv2, numpy as np
img = cv2.imread("/tmp/dots.png")
H, W = img.shape[:2]
print(f"Image: {W}x{H}")
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
# Red is H around 0 or 180 (wraps), S high, V high
# Red: H in [0,10] or [170,180], S > 100, V > 100
red1 = cv2.inRange(hsv, np.array((0, 100, 100)), np.array((10, 255, 255)))
red2 = cv2.inRange(hsv, np.array((170, 100, 100)), np.array((180, 255, 255)))
red_mask = cv2.bitwise_or(red1, red2)
print(f"Red pixels: {int((red_mask>0).sum())}")

# Find red contours
contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
print(f"Red contours: {len(contours)}")
for i, c in enumerate(sorted(contours, key=lambda c: -cv2.contourArea(c))[:5]):
    area = cv2.contourArea(c)
    x, y, w, h = cv2.boundingRect(c)
    print(f"  contour {i}: area={int(area)}  bbox=({x},{y},{w},{h})")
