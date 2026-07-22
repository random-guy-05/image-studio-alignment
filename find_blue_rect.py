"""Find the THIN BLUE RECTANGLE in the screenshot (the one the user just added)."""
import cv2, numpy as np
img = cv2.imread("/tmp/dots.png")
H, W = img.shape[:2]
print(f"Image: {W}x{H}")
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
blue_mask = cv2.inRange(hsv, np.array((100, 120, 100)), np.array((130, 255, 255)))
print(f"Blue pixels: {int((blue_mask>0).sum())}")

# Longest blue run per row (rectangle edges are long)
longest_h = np.zeros(H, dtype=int)
for y in range(H):
    row = blue_mask[y] > 0
    if not row.any(): continue
    padded = np.concatenate(([False], row, [False]))
    diffs = np.diff(padded.astype(int))
    starts = np.where(diffs == 1)[0]
    ends = np.where(diffs == -1)[0]
    runs = ends - starts
    if len(runs): longest_h[y] = runs.max()

# Longest per column
longest_v = np.zeros(W, dtype=int)
for x in range(W):
    col = blue_mask[:, x] > 0
    if not col.any(): continue
    padded = np.concatenate(([False], col, [False]))
    diffs = np.diff(padded.astype(int))
    starts = np.where(diffs == 1)[0]
    ends = np.where(diffs == -1)[0]
    runs = ends - starts
    if len(runs): longest_v[x] = runs.max()

# Top 10 rows by longest_h
print("\nTop 15 rows by horizontal blue run:")
for y in sorted(np.argsort(longest_h)[-15:][::-1]):
    print(f"  row {y}: h_run={longest_h[y]}  total_blue={int(blue_mask[y].sum()/255)}")

print("\nTop 15 cols by vertical blue run:")
for x in sorted(np.argsort(longest_v)[-15:][::-1]):
    print(f"  col {x}: v_run={longest_v[x]}  total_blue={int(blue_mask[:,x].sum()/255)}")
