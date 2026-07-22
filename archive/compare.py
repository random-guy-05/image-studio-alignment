"""Save current blue positions and compare with what the alignment was supposed to move them to."""
import json, subprocess, time
import cv2, numpy as np
import math

# Force ImageStudio front
for _ in range(5):
    subprocess.run(["osascript", "-e", 'tell application "ImageStudio" to activate'], check=True)
    time.sleep(0.3)

# Capture and detect
out = subprocess.check_output(["osascript", "-e",
    'tell application "System Events" to tell process "ImageStudio" to get position of front window & size of front window'
]).decode().strip()
nums = [int(x.strip()) for x in out.replace("{","").replace("}","").split(",")]
x, y, w, h = nums
subprocess.run(["screencapture", "-R", f"{x},{y},{w},{h}", "/tmp/post.png"], check=True)
img = cv2.imread("/tmp/post.png")
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
blue_mask = cv2.inRange(hsv, np.array((100, 120, 100)), np.array((130, 255, 255)))
bb = cv2.GaussianBlur(blue_mask, (5, 5), 1)
bc = cv2.HoughCircles(bb, cv2.HOUGH_GRADIENT, dp=1, minDist=20, param1=80, param2=15, minRadius=12, maxRadius=18)
post_blues = [] if bc is None else [(int(x), int(y)) for x, y, r in bc[0]]
print(f"POST blue count: {len(post_blues)}")

# Load the targets.json — dot positions are where the blue circles WERE before alignment
targets = json.load(open("/Users/admin/opencode-imagestudio/targets.json"))
pre_dots = [tuple(p["dot"]) for p in targets["pairs"]]  # in points
print(f"PRE blue count (pairs): {len(pre_dots)}")

# Convert pre_dots to physical pixels
scale = targets["scale"]
ox, oy = targets["bounds"][0], targets["bounds"][1]
pre_dots_phys = [(int((px-ox)*scale), int((py-oy)*scale)) for px, py in pre_dots]

# For each post blue, find the nearest pre_dot
print("\nMatching post blues to pre dots:")
post_to_pre = []
for bx, by in post_blues:
    nearest = None
    nd = float("inf")
    for i, (dx, dy) in enumerate(pre_dots_phys):
        d = math.hypot(bx-dx, by-dy)
        if d < nd:
            nd = d
            nearest = i
    post_to_pre.append((nearest, nd))

# How many post blues are within 30px of a pre dot? (= didn't move)
didnt_move = sum(1 for _, d in post_to_pre if d < 30)
moved_some = sum(1 for _, d in post_to_pre if 30 <= d < 200)
moved_far = sum(1 for _, d in post_to_pre if d >= 200)
print(f"Post blues still at pre position (d<30):    {didnt_move}")
print(f"Post blues at intermediate position (30-200): {moved_some}")
print(f"Post blues far from any pre position (>200):  {moved_far}")

# Also: for each pre dot, is there a post blue near its TARGET?
spot_pts = [tuple(p["spot"]) for p in targets["pairs"]]
spot_pts_phys = [(int((px-ox)*scale), int((py-oy)*scale)) for px, py in spot_pts]
on_spot = 0
for sx, sy in spot_pts_phys:
    for bx, by in post_blues:
        if math.hypot(sx-bx, sy-by) < 30:
            on_spot += 1
            break
print(f"\nPost blues within 30px of a target spot: {on_spot}/{len(spot_pts_phys)}")
print(f"  (expected ~209 if alignment worked; expected 0 if not)")
