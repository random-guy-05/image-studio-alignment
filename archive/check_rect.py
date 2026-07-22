import cv2, numpy as np
img = cv2.imread("/tmp/v8.png")
H, W = img.shape[:2]
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
blue_mask = cv2.inRange(hsv, np.array((100, 120, 100)), np.array((130, 255, 255)))
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
# Top 20 by longest_run
top = np.argsort(longest_run)[-20:][::-1]
print("Top 20 rows by longest blue run:")
for r in sorted(top):
    print(f"  row {r}: run={longest_run[r]}  total={int(blue_mask[r].sum()/255)}")
# Also: rows with run > 100
sig = np.where(longest_run > 100)[0]
print(f"\nRows with run > 100: {len(sig)}")
if len(sig): print(f"  {sig}")
# Total blue pixels
print(f"Total blue pixels: {int((blue_mask>0).sum())}")
