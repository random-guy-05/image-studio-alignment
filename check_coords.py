"""Check the screen's point size to determine the screenshot scale."""
import subprocess
out = subprocess.check_output(["osascript", "-e",
    'tell application "Finder" to get bounds of window of desktop'
]).decode().strip()
print(f"Screen bounds (points): {out}")
nums = [int(x.strip()) for x in out.replace("{","").replace("}","").split(",")]
screen_w_pts = nums[2] - nums[0]
screen_h_pts = nums[3] - nums[1]
print(f"Screen size (points): {screen_w_pts}x{screen_h_pts}")

import cv2
img = cv2.imread("/tmp/dots.png")
H, W = img.shape[:2]
print(f"Screenshot size (pixels): {W}x{H}")
print(f"Screenshot scale: {W/screen_w_pts:.2f}x")

# Also check the window capture scale
out2 = subprocess.check_output(["osascript", "-e",
    'tell application "System Events" to tell process "ImageStudio" to get position of every window & size of every window'
]).decode().strip()
nums2 = [int(x.strip()) for x in out2.replace("{","").replace("}","").split(",") if x.strip() not in ("missing value", "")]
n = len(nums2) // 4
windows = []
for i in range(n):
    x, y = nums2[i*2], nums2[i*2+1]
    w, h = nums2[n*2 + i*2], nums2[n*2 + i*2 + 1]
    if w > 0 and h > 0:
        windows.append((x, y, w, h, w*h))
windows.sort(key=lambda w: -w[4])
wx, wy, ww, wh = windows[0][:4]
print(f"\nMain window: ({wx},{wy}) {ww}x{wh} points")

# Capture the window and check its pixel size
subprocess.run(["screencapture", "-R", f"{wx},{wy},{ww},{wh}", "/tmp/winctest.png"], check=True)
wincap = cv2.imread("/tmp/winctest.png")
print(f"Window capture: {wincap.shape[1]}x{wincap.shape[0]} pixels")
print(f"Window capture scale: {wincap.shape[1]/ww:.2f}x")
