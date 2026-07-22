"""Check if the click coordinates still match the dot positions."""
import subprocess, time
import cv2, numpy as np
import json, math

# Get current window
for _ in range(3):
    subprocess.run(["osascript", "-e", 'tell application "ImageStudio" to activate'], check=True)
    time.sleep(0.3)

out = subprocess.check_output(["osascript", "-e",
    'tell application "System Events" to tell process "ImageStudio" to get position of front window & size of front window'
]).decode().strip()
nums = [int(x.strip()) for x in out.replace("{","").replace("}","").split(",")]
x, y, w, h = nums
print(f"CURRENT Window: {x},{y} {w}x{h}")

# Load targets
data = json.load(open("/Users/admin/opencode-imagestudio/targets.json"))
print(f"targets.json window bounds: {data['bounds']}")
print(f"  scale: {data['scale']}")
print(f"  pairs: {len(data['pairs'])}")

# Capture fresh
subprocess.run(["screencapture", "-R", f"{x},{y},{w},{h}", "/tmp/check.png"], check=True)
img = cv2.imread("/tmp/check.png")
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
blue_mask = cv2.inRange(hsv, np.array((100, 120, 100)), np.array((130, 255, 255)))
print(f"blue pixels in current capture: {int((blue_mask>0).sum())}")

# Find current blue circles
bb = cv2.GaussianBlur(blue_mask, (5, 5), 1)
bc = cv2.HoughCircles(bb, cv2.HOUGH_GRADIENT, dp=1, minDist=20, param1=80, param2=15, minRadius=12, maxRadius=18)
current_blues = [] if bc is None else [(int(x), int(y)) for x, y, r in bc[0]]
print(f"current blue circles: {len(current_blues)}")

# Compare with targets (in current capture coord system)
scale = data['scale']
ox, oy = data['bounds'][0], data['bounds'][1]
# Convert targets dot positions (in points) to physical pixels in CURRENT capture
# A point (px, py) is at physical pixel (px * scale, py * scale) RELATIVE to the window
# In the CURRENT capture, the window is at (x, y) in points = (x*scale, y*scale) in phys px
current_ox_phys = int(x * scale)
current_oy_phys = int(y * scale)
# But the targets are stored assuming the window was at (ox, oy) in points
# If the window has moved, we need to recompute

if (x, y) != (ox, oy):
    print(f"\n*** WINDOW HAS MOVED: was ({ox},{oy}), now ({x},{y}) — diff ({x-ox},{y-oy}) points")
    print("    targets.json coordinates are now MISALIGNED by this offset")

# Check: pick the first target dot and see if there's a blue at that screen position
first = data['pairs'][0]
dot_pt = first['dot']  # in points, relative to original window
# Convert to physical pixels in CURRENT capture
# The point (dot_pt) is at (dot_pt[0] * scale, dot_pt[1] * scale) in phys px FROM THE WINDOW ORIGIN
# The window origin in current capture is at (current_ox_phys, current_oy_phys)
target_phys = (int(dot_pt[0] * scale) - int(ox * scale) + current_ox_phys,
               int(dot_pt[1] * scale) - int(oy * scale) + current_oy_phys)
print(f"\nFirst target dot: point {dot_pt}  →  expected phys px in current capture: {target_phys}")

# Check the blue at that position
if 0 <= target_phys[0] < blue_mask.shape[1] and 0 <= target_phys[1] < blue_mask.shape[0]:
    px = blue_mask[target_phys[1], target_phys[0]]
    # Check a small area
    x0, y0 = max(0, target_phys[0]-20), max(0, target_phys[1]-20)
    x1, y1 = min(blue_mask.shape[1], target_phys[0]+20), min(blue_mask.shape[0], target_phys[1]+20)
    nearby_blue = int(blue_mask[y0:y1, x0:x1].sum() / 255)
    print(f"  blue at that exact pixel: {px}  (0=no blue, 255=blue)")
    print(f"  blue in 40x40 area around it: {nearby_blue} pixels")
