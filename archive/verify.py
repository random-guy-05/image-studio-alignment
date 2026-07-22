"""Verify alignment: capture fresh image, detect circles, check overlap."""
import subprocess, json
import cv2
import numpy as np

# Activate ImageStudio and capture
subprocess.run(["osascript", "-e", 'tell application "ImageStudio" to activate'], check=True)
import time
time.sleep(1)

# Capture just the window
out = subprocess.check_output(["osascript", "-e",
    'tell application "System Events" to tell process "ImageStudio" to get position of front window & size of front window'
]).decode().strip()
nums = [int(x.strip()) for x in out.replace("{","").replace("}","").split(",")]
x, y, w, h = nums
print(f"Window: {x},{y} {w}x{h}")

subprocess.run(["screencapture", "-R", f"{x},{y},{w},{h}", "/tmp/post.png"], check=True)
img = cv2.imread("/tmp/post.png")
print(f"Captured: {img.shape[1]}x{img.shape[0]}")

# Detect blue and grey
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
blue_mask = cv2.inRange(hsv, np.array((100, 120, 100)), np.array((130, 255, 255)))
grey_mask = cv2.inRange(hsv, np.array((0, 0, 180)), np.array((180, 20, 240)))

# Hough blue
bb = cv2.GaussianBlur(blue_mask, (5, 5), 1)
blue_circles = cv2.HoughCircles(bb, cv2.HOUGH_GRADIENT, dp=1, minDist=20,
                                 param1=80, param2=15, minRadius=12, maxRadius=18)
blue_circles = [] if blue_circles is None else [(int(x), int(y)) for x, y, r in blue_circles[0]]

# Hough grey
bg = cv2.GaussianBlur(grey_mask, (5, 5), 1)
grey_circles = cv2.HoughCircles(bg, cv2.HOUGH_GRADIENT, dp=1, minDist=20,
                                 param1=80, param2=25, minRadius=9, maxRadius=18)
grey_circles = [] if grey_circles is None else [(int(x), int(y)) for x, y, r in grey_circles[0]]

print(f"After alignment:  blue={len(blue_circles)}  grey={len(grey_circles)}")

# Check overlap: how many blue circles are within 30px of a grey circle?
import math
overlapping = 0
for bx, by in blue_circles:
    for gx, gy in grey_circles:
        if math.hypot(bx - gx, by - gy) < 30:
            overlapping += 1
            break
print(f"Blue circles within 30px of a grey spot: {overlapping}/{len(blue_circles)}")
print(f"Match rate: {100*overlapping/len(blue_circles):.0f}%" if blue_circles else "")

# Save overlay
overlay = img.copy()
for bx, by in blue_circles:
    cv2.circle(overlay, (bx, by), 22, (0, 255, 0), 2)  # green = blue dot
for gx, gy in grey_circles:
    cv2.circle(overlay, (gx, gy), 22, (0, 0, 255), 2)  # red = grey spot
cv2.imwrite("/tmp/post-overlay.png", overlay)
print("Saved /tmp/post-overlay.png")
