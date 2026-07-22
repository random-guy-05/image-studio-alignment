import subprocess, time, json, math
import cv2, numpy as np

for _ in range(3):
    subprocess.run(["osascript", "-e", 'tell application "ImageStudio" to activate'], check=True)
    time.sleep(0.3)

out = subprocess.check_output(["osascript", "-e",
    'tell application "System Events" to tell process "ImageStudio" to get position of front window & size of front window'
]).decode().strip()
nums = [int(x.strip()) for x in out.replace("{","").replace("}","").split(",")]
wx, wy, ww, wh = nums
print(f"Window: ({wx},{wy}) {ww}x{wh}")
subprocess.run(["screencapture", "-R", f"{wx},{wy},{ww},{wh}", "/tmp/v5.png"], check=True)
img = cv2.imread("/tmp/v5.png")
H, W = img.shape[:2]
scale = W / ww
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
blue_mask = cv2.inRange(hsv, np.array((100, 120, 100)), np.array((130, 255, 255)))
bb = cv2.GaussianBlur(blue_mask, (5, 5), 1)
bc = cv2.HoughCircles(bb, cv2.HOUGH_GRADIENT, dp=1, minDist=20, param1=80, param2=15, minRadius=6, maxRadius=18)
current = [] if bc is None else [(int(x), int(y)) for x, y, r in bc[0]]
print(f"Current blues: {len(current)}")

targets = json.load(open("/Users/admin/opencode-imagestudio/targets.json"))
pairs = targets["pairs"]

# Check: for each target spot, is there a blue within 15px?
on_target = 0
for p in pairs:
    sx, sy = p["spot"]
    spx, spy = int((sx-wx)*scale), int((sy-wy)*scale)
    for bx, by in current:
        if math.hypot(bx-spx, by-spy) < 15:
            on_target += 1
            break
print(f"Targets now occupied by a blue (within 15px): {on_target}/{len(pairs)}")

# Original positions
still_origin = 0
for p in pairs:
    dx, dy = p["dot"]
    dpx, dpy = int((dx-wx)*scale), int((dy-wy)*scale)
    for bx, by in current:
        if math.hypot(bx-dpx, by-dpy) < 15:
            still_origin += 1
            break
print(f"Original positions still occupied: {still_origin}/{len(pairs)}")
