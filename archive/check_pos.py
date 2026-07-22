"""Check what's actually at the first few target positions."""
import json, subprocess
import cv2
import numpy as np

# Capture current window
out = subprocess.check_output(["osascript", "-e",
    'tell application "System Events" to tell process "ImageStudio" to get position of front window & size of front window'
]).decode().strip()
nums = [int(x.strip()) for x in out.replace("{","").replace("}","").split(",")]
wx, wy, ww, wh = nums
print(f"Window: ({wx},{wy}) {ww}x{wh}")
subprocess.run(["screencapture", "-R", f"{wx},{wy},{ww},{wh}", "/tmp/check2.png"], check=True)

img = cv2.imread("/tmp/check2.png")
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
scale = 2.0  # phys px per point

data = json.load(open("/Users/admin/opencode-imagestudio/targets.json"))
print(f"\nFirst 5 pairs — what's at each position:")
print(f"{'i':>3}  {'dot(pt)':>12}  {'spot(pt)':>12}  {'dist':>5}  {'at dot':>20}  {'at spot':>20}")
for i, p in enumerate(data["pairs"][:5]):
    dx, dy = p["dot"]
    sx, sy = p["spot"]
    dist = ((sx-dx)**2 + (sy-dy)**2)**0.5
    # Convert to phys px in capture
    dpx, dpy = int((dx-wx)*scale), int((dy-wy)*scale)
    spx, spy = int((sx-wx)*scale), int((sy-wy)*scale)
    # Sample a 5x5 area at each
    def sample(x, y):
        if 0 <= x < img.shape[1] and 0 <= y < img.shape[0]:
            patch = img[max(0,y-2):y+3, max(0,x-2):x+3]
            # Find dominant color
            mean = patch.mean(axis=(0,1))
            h_patch = hsv[max(0,y-2):y+3, max(0,x-2):x+3].mean(axis=(0,1))
            return f"HSV({int(h_patch[0])},{int(h_patch[1])},{int(h_patch[2])})"
        return "OOB"
    print(f"{i:>3}  ({dx:>3},{dy:>3})    ({sx:>3},{sy:>3})    {dist:>5.0f}  {sample(dpx, dpy):>20}  {sample(spx, spy):>20}")
