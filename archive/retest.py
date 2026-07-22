"""Test detection on the fresh capture."""
import cv2, numpy as np

img = cv2.imread("/tmp/imagestudio2.png")
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

blue_mask = cv2.inRange(hsv, np.array((100, 120, 100)), np.array((130, 255, 255)))
print("blue_mask nonzero:", int((blue_mask > 0).sum()))

grey_mask = cv2.inRange(hsv, np.array((0, 0, 180)), np.array((180, 20, 240)))
print("grey_mask nonzero:", int((grey_mask > 0).sum()))

# Hough blue
blurred_b = cv2.GaussianBlur(blue_mask, (5, 5), 1)
c = cv2.HoughCircles(blurred_b, cv2.HOUGH_GRADIENT, dp=1, minDist=20,
                     param1=80, param2=15, minRadius=12, maxRadius=18)
print(f"blue hough: {0 if c is None else len(c[0])}")

# Hough grey
blurred_g = cv2.GaussianBlur(grey_mask, (5, 5), 1)
c = cv2.HoughCircles(blurred_g, cv2.HOUGH_GRADIENT, dp=1, minDist=20,
                     param1=80, param2=25, minRadius=9, maxRadius=18)
print(f"grey hough: {0 if c is None else len(c[0])}")

# Save the new image
import shutil
shutil.copy("/tmp/imagestudio2.png", "/tmp/imagestudio.png")
print("copied to /tmp/imagestudio.png")
