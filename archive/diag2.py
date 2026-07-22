"""Full diagnostic on the current screen state."""
import subprocess
import cv2
import numpy as np

# Activate and capture
subprocess.run(["osascript", "-e", 'tell application "ImageStudio" to activate'], check=True)
import time
time.sleep(1)

# Full screen
subprocess.run(["screencapture", "-x", "/tmp/full2.png"], check=True)
full = cv2.imread("/tmp/full2.png")
print(f"Full screen: {full.shape[1]}x{full.shape[0]}")

# Just the window
out = subprocess.check_output(["osascript", "-e",
    'tell application "System Events" to tell process "ImageStudio" to get position of front window & size of front window'
]).decode().strip()
nums = [int(x.strip()) for x in out.replace("{","").replace("}","").split(",")]
x, y, w, h = nums
print(f"Window: {x},{y} {w}x{h}")
subprocess.run(["screencapture", "-R", f"{x},{y},{w},{h}", "/tmp/win2.png"], check=True)
win = cv2.imread("/tmp/win2.png")
print(f"Window capture: {win.shape[1]}x{win.shape[0]}")

# How many blue pixels?
hsv = cv2.cvtColor(win, cv2.COLOR_BGR2HSV)
blue_mask = cv2.inRange(hsv, np.array((100, 120, 100)), np.array((130, 255, 255)))
grey_mask = cv2.inRange(hsv, np.array((0, 0, 180)), np.array((180, 20, 240)))
print(f"blue pixels: {int((blue_mask>0).sum())}")
print(f"grey pixels: {int((grey_mask>0).sum())}")

# Hough
bb = cv2.GaussianBlur(blue_mask, (5, 5), 1)
c = cv2.HoughCircles(bb, cv2.HOUGH_GRADIENT, dp=1, minDist=20,
                     param1=80, param2=15, minRadius=12, maxRadius=18)
print(f"blue hough: {0 if c is None else len(c[0])}")

bg = cv2.GaussianBlur(grey_mask, (5, 5), 1)
c = cv2.HoughCircles(bg, cv2.HOUGH_GRADIENT, dp=1, minDist=20,
                     param1=80, param2=25, minRadius=9, maxRadius=18)
print(f"grey hough: {0 if c is None else len(c[0])}")
