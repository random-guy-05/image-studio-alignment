import cv2, numpy as np
img = cv2.imread("/tmp/dots.png")
H, W = img.shape[:2]
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
blue_mask = cv2.inRange(hsv, np.array((100, 120, 100)), np.array((130, 255, 255)))

# Find the blue rectangle: long horizontal + vertical runs
longest_h = np.zeros(H, dtype=int)
for y in range(H):
    row = blue_mask[y] > 0
    if not row.any(): continue
    padded = np.concatenate(([False], row, [False]))
    diffs = np.diff(padded.astype(int))
    starts = np.where(diffs == 1)[0]; ends = np.where(diffs == -1)[0]
    if len(starts): longest_h[y] = (ends - starts).max()

longest_v = np.zeros(W, dtype=int)
for x in range(W):
    col = blue_mask[:, x] > 0
    if not col.any(): continue
    padded = np.concatenate(([False], col, [False]))
    diffs = np.diff(padded.astype(int))
    starts = np.where(diffs == 1)[0]; ends = np.where(diffs == -1)[0]
    if len(starts): longest_v[x] = (ends - starts).max()

# Rows with long h-runs
h_thresh = 100
h_rows = np.where(longest_h > h_thresh)[0]
v_cols = np.where(longest_v > h_thresh)[0]
print(f"Rows with h_run > {h_thresh}: {h_rows}")
print(f"Cols with v_run > {h_thresh}: {v_cols}")

# If we have 2 h-rows and 2 v-cols, that's the rectangle
if len(h_rows) >= 2 and len(v_cols) >= 2:
    top = h_rows.min()
    bot = h_rows.max()
    left = v_cols.min()
    right = v_cols.max()
    print(f"\nBLUE RECTANGLE: x=[{left},{right}]  y=[{top},{bot}]")
    print(f"  width={right-left}  height={bot-top}")
