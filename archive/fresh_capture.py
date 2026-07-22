"""Fresh detection on the current window state."""
import subprocess, time
import cv2, numpy as np
import json, math

# Activate
for _ in range(3):
    subprocess.run(["osascript", "-e", 'tell application "ImageStudio" to activate'], check=True)
    time.sleep(0.3)

out = subprocess.check_output(["osascript", "-e",
    'tell application "System Events" to tell process "ImageStudio" to get position of front window & size of front window'
]).decode().strip()
nums = [int(x.strip()) for x in out.replace("{","").replace("}","").split(",")]
x, y, w, h = nums
print(f"Window: {x},{y} {w}x{h}")

subprocess.run(["screencapture", "-R", f"{x},{y},{w},{h}", "/tmp/fresh.png"], check=True)
img = cv2.imread("/tmp/fresh.png")
print(f"Captured: {img.shape[1]}x{img.shape[0]}")

hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
blue_mask = cv2.inRange(hsv, np.array((100, 120, 100)), np.array((130, 255, 255)))
grey_mask = cv2.inRange(hsv, np.array((0, 0, 180)), np.array((180, 20, 240)))
print(f"blue pixels: {int((blue_mask>0).sum())}")
print(f"grey pixels: {int((grey_mask>0).sum())}")

bb = cv2.GaussianBlur(blue_mask, (5, 5), 1)
bc = cv2.HoughCircles(bb, cv2.HOUGH_GRADIENT, dp=1, minDist=20, param1=80, param2=15, minRadius=12, maxRadius=18)
blue_n = 0 if bc is None else len(bc[0])
bg = cv2.GaussianBlur(grey_mask, (5, 5), 1)
gc = cv2.HoughCircles(bg, cv2.HOUGH_GRADIENT, dp=1, minDist=20, param1=80, param2=25, minRadius=9, maxRadius=18)
grey_n = 0 if gc is None else len(gc[0])
print(f"blue hough: {blue_n}    grey hough: {grey_n}")
print(f"Saved /tmp/fresh.png")
