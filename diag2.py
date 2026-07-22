"""Quick diagnostic: what do the data dots actually look like in the screenshot?"""
import cv2, numpy as np
img = cv2.imread("/tmp/dots.png")
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
# Try multiple V thresholds and count
for v_max in [150, 180, 200, 220, 240]:
    mask = cv2.inRange(hsv, np.array((0, 0, 0)), np.array((180, 50, v_max)))
    num, labels, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
    # Filter: area 20-300 (typical data dot size)
    real = sum(1 for i in range(1, num) if 20 <= stats[i][4] <= 300)
    print(f"V<{v_max}: total={num-1}  area 20-300: {real}")

# Also: try HoughCircles on the data
print("\nHoughCircles on data (different params):")
for v_max, p2 in [(200, 12), (200, 15), (180, 12), (150, 12)]:
    mask = cv2.inRange(hsv, np.array((0, 0, 0)), np.array((180, 50, v_max)))
    blurred = cv2.GaussianBlur(mask, (5, 5), 1)
    circles = cv2.HoughCircles(blurred, cv2.HOUGH_GRADIENT, dp=1, minDist=15,
                                 param1=80, param2=p2, minRadius=3, maxRadius=15)
    n = 0 if circles is None else len(circles[0])
    print(f"  V<{v_max} p2={p2}: {n} circles")

# Also check the current ImageStudio view
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
    windows.append((x, y, w, h))
windows.sort(key=lambda w: -w[3]*w[4])
wx, wy, ww, wh = windows[0][:4]
print(f"\nImageStudio main window: ({wx},{wy}) {ww}x{wh}")
subprocess.run(["screencapture", "-R", f"{wx},{wy},{ww},{wh}", "/tmp/cur.png"], check=True)
cur = cv2.imread("/tmp/cur.png")
cur_hsv = cv2.cvtColor(cur, cv2.COLOR_BGR2HSV)
blue_mask = cv2.inRange(cur_hsv, np.array((100, 120, 100)), np.array((130, 255, 255)))
# Find blue circles with looser params
blurred = cv2.GaussianBlur(blue_mask, (5, 5), 1)
for p2, rmin, rmax in [(12, 6, 18), (8, 4, 20), (15, 6, 18)]:
    circles = cv2.HoughCircles(blurred, cv2.HOUGH_GRADIENT, dp=1, minDist=12,
                                 param1=80, param2=p2, minRadius=rmin, maxRadius=rmax)
    n = 0 if circles is None else len(circles[0])
    print(f"  blue p2={p2} r={rmin}-{rmax}: {n}")
