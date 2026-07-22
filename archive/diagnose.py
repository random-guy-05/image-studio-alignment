"""Diagnose what's in the captured image vs what's on screen."""
import subprocess, json
import cv2
import numpy as np

# Get screen size via AppleScript
out = subprocess.check_output(["osascript", "-e",
    'tell application "Finder" to get bounds of window of desktop']).decode().strip()
print("Screen bounds (Finder desktop):", out)

# Take a full-screen screenshot
subprocess.run(["screencapture", "-x", "/tmp/full.png"], check=True)
full = cv2.imread("/tmp/full.png")
print("Full screen image shape (HxWxC):", full.shape)

# Get ImageStudio window position and size in points
bounds_out = subprocess.check_output(["osascript", "-e",
    'tell application "System Events" to tell process "ImageStudio" to get position of front window & size of front window']).decode().strip()
print("ImageStudio bounds raw:", repr(bounds_out))
nums = [int(x.strip()) for x in bounds_out.replace("{","").replace("}","").split(",")]
x, y, w, h = nums
print(f"ImageStudio: x={x}, y={y}, w={w}, h={h}")

# The captured /tmp/imagestudio.png from detect.py
cap = cv2.imread("/tmp/imagestudio.png")
print("Captured image shape:", cap.shape)

# Compute scale factor
print(f"Scale: captured W {cap.shape[1]} / bounds W {w} = {cap.shape[1]/w:.2f}")
print(f"Scale: captured H {cap.shape[0]} / bounds H {h} = {cap.shape[0]/h:.2f}")

# Find where blue pixels are in the captured image
hsv = cv2.cvtColor(cap, cv2.COLOR_BGR2HSV)
mask = cv2.inRange(hsv, np.array((100, 120, 100)), np.array((130, 255, 255)))
ys, xs = np.where(mask > 0)
if len(xs):
    print(f"Blue pixels in capture: count={len(xs)}, x range [{xs.min()}, {xs.max()}], y range [{ys.min()}, {ys.max()}]")
else:
    print("NO blue pixels in capture!")

# Where are blue pixels in the full screen?
hsv_full = cv2.cvtColor(full, cv2.COLOR_BGR2HSV)
mask_full = cv2.inRange(hsv_full, np.array((100, 120, 100)), np.array((130, 255, 255)))
ys2, xs2 = np.where(mask_full > 0)
if len(xs2):
    print(f"Blue pixels in FULL screen: count={len(xs2)}, x range [{xs2.min()}, {xs2.max()}], y range [{ys2.min()}, {ys2.max()}]")
else:
    print("NO blue pixels in full screen either!")

# Find grey pixels in full screen
mask_grey = cv2.inRange(hsv_full, np.array((0, 0, 60)), np.array((180, 40, 200)))
ys3, xs3 = np.where(mask_grey > 0)
if len(xs3):
    print(f"Grey pixels in FULL screen: count={len(xs3)}, x range [{xs3.min()}, {xs3.max()}], y range [{ys3.min()}, {ys3.max()}]")
