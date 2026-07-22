import cv2, numpy as np
import subprocess
out = subprocess.check_output(["osascript", "-e",
    'tell application "System Events" to tell process "ImageStudio" to get position of front window & size of front window'
]).decode().strip()
nums = [int(x.strip()) for x in out.replace("{","").replace("}","").split(",")]
wx, wy, ww, wh = nums
print(f"Window: ({wx},{wy}) {ww}x{wh}")
subprocess.run(["screencapture", "-R", f"{wx},{wy},{ww},{wh}", "/tmp/v7.png"], check=True)
img = cv2.imread("/tmp/v7.png")
H, W = img.shape[:2]
print(f"Image: {W}x{H}")
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
blue_mask = cv2.inRange(hsv, np.array((100, 120, 100)), np.array((130, 255, 255)))
# Longest run per row
longest_run = np.zeros(H, dtype=int)
for y in range(H):
    row = blue_mask[y] > 0
    if not row.any(): continue
    padded = np.concatenate(([False], row, [False]))
    diffs = np.diff(padded.astype(int))
    starts = np.where(diffs == 1)[0]
    ends = np.where(diffs == -1)[0]
    runs = ends - starts
    if len(runs): longest_run[y] = runs.max()
# Top rows by longest_run
top = np.argsort(longest_run)[-10:][::-1]
for r in sorted(top):
    print(f"  row {r}: run={longest_run[r]}  total_blue={int(blue_mask[r].sum()/255)}")
# Rows with run > 100
sig = np.where(longest_run > 100)[0]
print(f"\nRows with run > 100: {len(sig)}")
if len(sig): print(f"  {sig}")
