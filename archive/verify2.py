"""Robust verify: force ImageStudio to front, wait until it's actually front, then capture."""
import subprocess, time
import cv2, numpy as np
import math

# Force ImageStudio to front
subprocess.run(["osascript", "-e", 'tell application "ImageStudio" to activate'], check=True)

# Poll until ImageStudio is actually frontmost
for _ in range(20):
    front = subprocess.check_output(["osascript", "-e",
        'tell application "System Events" to get name of every process whose frontmost is true'
    ]).decode().strip()
    if "ImageStudio" in front or "JavaApplicationStub" in front:
        break
    subprocess.run(["osascript", "-e", 'tell application "ImageStudio" to activate'], check=True)
    time.sleep(0.3)
print(f"Frontmost: {front}")

# Capture window
out = subprocess.check_output(["osascript", "-e",
    'tell application "System Events" to tell process "ImageStudio" to get position of front window & size of front window'
]).decode().strip()
nums = [int(x.strip()) for x in out.replace("{","").replace("}","").split(",")]
x, y, w, h = nums
print(f"Window: {x},{y} {w}x{h}")

# Capture
subprocess.run(["screencapture", "-R", f"{x},{y},{w},{h}", "/tmp/post.png"], check=True)
img = cv2.imread("/tmp/post.png")
print(f"Captured: {img.shape[1]}x{img.shape[0]}")

# Sanity check on capture (should NOT look like a terminal)
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
blue_mask = cv2.inRange(hsv, np.array((100, 120, 100)), np.array((130, 255, 255)))
grey_mask = cv2.inRange(hsv, np.array((0, 0, 180)), np.array((180, 20, 240)))
print(f"blue pixels: {int((blue_mask>0).sum())}")
print(f"grey pixels: {int((grey_mask>0).sum())}")

# Hough blue
bb = cv2.GaussianBlur(blue_mask, (5, 5), 1)
bc = cv2.HoughCircles(bb, cv2.HOUGH_GRADIENT, dp=1, minDist=20, param1=80, param2=15, minRadius=12, maxRadius=18)
blue_circles = [] if bc is None else [(int(x), int(y)) for x, y, r in bc[0]]

# Hough grey
bg = cv2.GaussianBlur(grey_mask, (5, 5), 1)
gc = cv2.HoughCircles(bg, cv2.HOUGH_GRADIENT, dp=1, minDist=20, param1=80, param2=25, minRadius=9, maxRadius=18)
grey_circles = [] if gc is None else [(int(x), int(y)) for x, y, r in gc[0]]

print(f"\nAfter alignment:  blue={len(blue_circles)}  grey={len(grey_circles)}")

# Overlap
overlapping = 0
for bx, by in blue_circles:
    for gx, gy in grey_circles:
        if math.hypot(bx - gx, by - gy) < 30:
            overlapping += 1
            break
print(f"Blue within 30px of grey: {overlapping}/{len(blue_circles)}")
if blue_circles:
    print(f"Match rate: {100*overlapping/len(blue_circles):.1f}%")

# Save overlay
overlay = img.copy()
for bx, by in blue_circles:
    cv2.circle(overlay, (bx, by), 22, (0, 255, 0), 2)
for gx, gy in grey_circles:
    cv2.circle(overlay, (gx, gy), 22, (0, 0, 255), 2)
cv2.imwrite("/tmp/post-overlay.png", overlay)
print("Saved /tmp/post-overlay.png")
