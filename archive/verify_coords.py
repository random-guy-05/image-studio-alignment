"""Verify the first 5 target dots have blue circles at the exact pixel positions."""
import json, subprocess, time
import cv2, numpy as np
import math

# Get current window
out = subprocess.check_output(["osascript", "-e",
    'tell application "System Events" to tell process "ImageStudio" to get position of front window & size of front window'
]).decode().strip()
nums = [int(x.strip()) for x in out.replace("{","").replace("}","").split(",")]
wx, wy, ww, wh = nums
print(f"Window: ({wx},{wy}) {ww}x{wh}")

# Load targets (should be in points relative to the current window)
data = json.load(open("/Users/admin/opencode-imagestudio/targets.json"))
scale = data["scale"]

# Capture
subprocess.run(["screencapture", "-R", f"{wx},{wy},{ww},{wh}", "/tmp/verify.png"], check=True)
img = cv2.imread("/tmp/verify.png")
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
blue_mask = cv2.inRange(hsv, np.array((100, 120, 100)), np.array((130, 255, 255)))

# Check first 5 pairs
print("\nVerifying first 5 dot positions:")
for i, p in enumerate(data["pairs"][:5]):
    dx, dy = p["dot"]
    # Convert point (dx, dy) to physical pixel in capture: window-relative * scale
    px, py = int((dx - wx) * scale), int((dy - wy) * scale)
    if 0 <= px < blue_mask.shape[1] and 0 <= py < blue_mask.shape[0]:
        # Count blue in 30x30 area
        x0, y0 = max(0, px-15), max(0, py-15)
        x1, y1 = min(blue_mask.shape[1], px+15), min(blue_mask.shape[0], py+15)
        nearby = int(blue_mask[y0:y1, x0:x1].sum() / 255)
        status = "OK" if nearby > 100 else "MISSING"
        print(f"  {i}: dot point ({dx},{dy}) → phys px ({px},{py})  blue_in_30px: {nearby}  [{status}]")
    else:
        print(f"  {i}: dot point ({dx},{dy}) → phys px ({px},{py})  OUT OF BOUNDS")
