"""Analyze the screenshot: size distribution of connected components."""
import cv2, numpy as np
img = cv2.imread("/tmp/dots.png")
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
data_mask = cv2.inRange(hsv, np.array((0, 0, 0)), np.array((180, 50, 200)))
num, labels, stats, cents = cv2.connectedComponentsWithStats(data_mask, 8)
sizes = sorted([stats[i][4] for i in range(1, num)], reverse=True)
print(f"Total components: {num-1}")
print(f"Top 30 areas: {sizes[:30]}")
# Histogram
bins = [0, 5, 10, 20, 50, 100, 200, 500, 1000, 5000]
for lo, hi in zip(bins[:-1], bins[1:]):
    count = sum(1 for s in sizes if lo <= s < hi)
    print(f"  {lo}-{hi}: {count}")
# Also check: how many are > 20 pixels (real data dots)
real = sum(1 for s in sizes if 20 <= s <= 500)
print(f"\nLikely real data dots (area 20-500): {real}")

# Also: capture the current ImageStudio view and count blue circles
import subprocess
out = subprocess.check_output(["osascript", "-e",
    'tell application "System Events" to tell process "ImageStudio" to get position of every window & size of every window'
]).decode().strip()
nums = [int(x.strip()) for x in out.replace("{","").replace("}","").split(",")]
n = len(nums) // 4
windows = []
for i in range(n):
    x, y = nums[i*2], nums[i*2+1]
    w, h = nums[n*2 + i*2], nums[n*2 + i*2 + 1]
    windows.append((x, y, w, h, w*h))
windows.sort(key=lambda w: -w[4])
print(f"\nImageStudio windows: {[(x,y,w,h) for x,y,w,h,_ in windows]}")
wx, wy, ww, wh = windows[0][:4]
subprocess.run(["screencapture", "-R", f"{wx},{wy},{ww},{wh}", "/tmp/current.png"], check=True)
cur = cv2.imread("/tmp/current.png")
print(f"Current capture: {cur.shape[1]}x{cur.shape[0]}")
# Count blue pixels per row to see if the grid is visible
cur_hsv = cv2.cvtColor(cur, cv2.COLOR_BGR2HSV)
cur_blue = cv2.inRange(cur_hsv, np.array((100, 120, 100)), np.array((130, 255, 255)))
print(f"Blue pixels in current view: {int((cur_blue>0).sum())}")
# Find blue circles
cur_bb = cv2.GaussianBlur(cur_blue, (5, 5), 1)
r_min, r_max = 6, 18
cur_circles = cv2.HoughCircles(cur_bb, cv2.HOUGH_GRADIENT, dp=1, minDist=15, param1=80, param2=12, minRadius=r_min, maxRadius=r_max)
n_cur = 0 if cur_circles is None else len(cur_circles[0])
print(f"Blue circles in current view: {n_cur}")
