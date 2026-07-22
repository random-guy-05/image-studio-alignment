"""Verify: did the 28 blues move to their targets?"""
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
wx, wy, ww, wh = nums
print(f"Window: ({wx},{wy}) {ww}x{wh}")

subprocess.run(["screencapture", "-R", f"{wx},{wy},{ww},{wh}", "/tmp/after.png"], check=True)
img = cv2.imread("/tmp/after.png")
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
scale = 2.0

# Detect current blues
blue_mask = cv2.inRange(hsv, np.array((100, 120, 100)), np.array((130, 255, 255)))
bb = cv2.GaussianBlur(blue_mask, (5, 5), 1)
bc = cv2.HoughCircles(bb, cv2.HOUGH_GRADIENT, dp=1, minDist=20, param1=80, param2=15, minRadius=12, maxRadius=18)
current = [] if bc is None else [(int(x), int(y)) for x, y, r in bc[0]]
print(f"Current blue circles: {len(current)}")

# Load the 28 pairs we tried to align
targets = json.load(open("/Users/admin/opencode-imagestudio/targets.json"))
pairs = targets["pairs"]
print(f"Targets to align: {len(pairs)}")

# For each target spot, is there a blue within 20 phys px (= 10 points)?
on_target = 0
for p in pairs:
    sx, sy = p["spot"]
    spx, spy = int((sx-wx)*scale), int((sy-wy)*scale)
    for bx, by in current:
        if math.hypot(bx-spx, by-spy) < 25:
            on_target += 1
            break
print(f"Targets now occupied by a blue: {on_target}/{len(pairs)}")

# Also: for each original dot, is there STILL a blue there? (= didn't move)
still_at_origin = 0
for p in pairs:
    dx, dy = p["dot"]
    dpx, dpy = int((dx-wx)*scale), int((dy-wy)*scale)
    for bx, by in current:
        if math.hypot(bx-dpx, by-dpy) < 25:
            still_at_origin += 1
            break
print(f"Original dot positions still occupied: {still_at_origin}/{len(pairs)}  (lower = more moved)")

# Total blues on any target (light grey or black within 20px)
grey_light = cv2.inRange(hsv, np.array((0, 0, 180)), np.array((180, 20, 240)))
grey_black = cv2.inRange(hsv, np.array((0, 0, 0)),   np.array((180, 60,  60)))
grey_mask = cv2.bitwise_or(grey_light, grey_black)
blues_on_any_grey = 0
for bx, by in current:
    # check 20px area for grey
    x0, y0 = max(0, bx-20), max(0, by-20)
    x1, y1 = min(grey_mask.shape[1], bx+20), min(grey_mask.shape[0], by+20)
    if int(grey_mask[y0:y1, x0:x1].sum() / 255) > 50:
        blues_on_any_grey += 1
print(f"\nTotal blues sitting on a grey/black spot: {blues_on_any_grey}/{len(current)}")
