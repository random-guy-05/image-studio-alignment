"""Show all rows with longest_run > 50, to find the two thin lines."""
import cv2, numpy as np
img = cv2.imread("/tmp/v4.png")
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
blue_mask = cv2.inRange(hsv, np.array((100, 120, 100)), np.array((130, 255, 255)))
H, W = blue_mask.shape

longest_run = np.zeros(H, dtype=int)
for y in range(H):
    row = blue_mask[y] > 0
    if not row.any():
        continue
    padded = np.concatenate(([False], row, [False]))
    diffs = np.diff(padded.astype(int))
    starts = np.where(diffs == 1)[0]
    ends = np.where(diffs == -1)[0]
    runs = ends - starts
    if len(runs):
        longest_run[y] = runs.max()

# All rows with run > 50, grouped
significant = np.where(longest_run > 50)[0]
print(f"Rows with longest_run > 50: {len(significant)}")
groups = [[significant[0]]] if len(significant) > 0 else []
for r in significant[1:]:
    if r - groups[-1][-1] <= 3:
        groups[-1].append(r)
    else:
        groups.append([r])
print(f"Groups: {len(groups)}")
for g in groups:
    print(f"  rows {g[0]}-{g[-1]}  (width {g[-1]-g[0]+1})  max_run={int(longest_run[g[0]:g[-1]+1].max())}  total_blue_rows={int(blue_mask[g[0]:g[-1]+1].sum()/255)}")
