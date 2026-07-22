"""Look at the current state after alignment."""
import cv2, numpy as np

img = cv2.imread("/tmp/post-overlay.png")  # this is actually the window capture saved by verify.py
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

# Color distribution
print(f"Image size: {img.shape[1]}x{img.shape[0]}")
print(f"blue pixels: {int((cv2.inRange(hsv, np.array((100,120,100)), np.array((130,255,255)))>0).sum())}")
print(f"grey pixels (V>=180): {int((cv2.inRange(hsv, np.array((0,0,180)), np.array((180,20,240)))>0).sum())}")
print(f"very dark pixels: {int((cv2.inRange(hsv, np.array((0,0,0)), np.array((180,255,50)))>0).sum())}")

# Sample colors at various positions
print("\nColor samples (BGR values, 0-255):")
for y_pct in [0.2, 0.4, 0.6, 0.8]:
    for x_pct in [0.2, 0.4, 0.6, 0.8]:
        y = int(img.shape[0] * y_pct)
        x = int(img.shape[1] * x_pct)
        bgr = img[y, x]
        h, s, v = hsv[y, x]
        print(f"  ({x_pct},{y_pct}) HSV=({h},{s},{v}) BGR={tuple(int(c) for c in bgr)}")
