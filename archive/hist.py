"""Color histogram to understand the current state."""
import cv2
import numpy as np

win = cv2.imread("/tmp/win2.png")
hsv = cv2.cvtColor(win, cv2.COLOR_BGR2HSV)

# Bins
print("HSV V (value) histogram:")
v = hsv[:,:,2]
hist, bins = np.histogram(v, bins=10, range=(0, 256))
for i, count in enumerate(hist):
    print(f"  V {i*25}-{(i+1)*25}: {count} pixels")

# Check the top-left and center of the window
print("\nSamples at fixed positions:")
for y_pct in [0.1, 0.3, 0.5, 0.7, 0.9]:
    for x_pct in [0.1, 0.3, 0.5, 0.7, 0.9]:
        y = int(win.shape[0] * y_pct)
        x = int(win.shape[1] * x_pct)
        h, s, v = hsv[y, x]
        bgr = win[y, x]
        print(f"  ({x_pct:.1f},{y_pct:.1f}) = ({x},{y}): HSV=({h},{s},{v}) BGR={tuple(int(c) for c in bgr)}")
