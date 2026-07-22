"""Check the new screenshot: what's the rectangle situation?"""
import cv2, numpy as np
img = cv2.imread("/tmp/dots.png")
H, W = img.shape[:2]
print(f"Image: {W}x{H}")
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
blue_mask = cv2.inRange(hsv, np.array((100, 120, 100)), np.array((130, 255, 255)))
print(f"Blue pixels: {int((blue_mask>0).sum())}")

# Find longest blue runs
lh = np.zeros(H, dtype=int)
for y in range(H):
    row = blue_mask[y] > 0
    if not row.any(): continue
    padded = np.concatenate(([False], row, [False]))
    diffs = np.diff(padded.astype(int))
    starts = np.where(diffs == 1)[0]; ends = np.where(diffs == -1)[0]
    if len(starts): lh[y] = (ends - starts).max()

lv = np.zeros(W, dtype=int)
for x in range(W):
    col = blue_mask[:, x] > 0
    if not col.any(): continue
    padded = np.concatenate(([False], col, [False]))
    diffs = np.diff(padded.astype(int))
    starts = np.where(diffs == 1)[0]; ends = np.where(diffs == -1)[0]
    if len(starts): lv[x] = (ends - starts).max()

# Try different thresholds
for t in [10, 30, 50, 100, 200]:
    h_rows = np.where(lh > t)[0]
    v_cols = np.where(lv > t)[0]
    if len(h_rows) >= 2 and len(v_cols) >= 2:
        print(f"  thresh={t}: h_rows range [{h_rows.min()},{h_rows.max()}]  v_cols range [{v_cols.min()},{v_cols.max()}]")
        # Cluster
        h_clusters = [[h_rows[0]]]
        for r in h_rows[1:]:
            if r - h_clusters[-1][-1] <= 3: h_clusters[-1].append(r)
            else: h_clusters.append([r])
        v_clusters = [[v_cols[0]]]
        for c in v_cols[1:]:
            if c - v_clusters[-1][-1] <= 3: v_clusters[-1].append(c)
            else: v_clusters.append([c])
        # Show top 2 of each
        h_top = sorted(h_clusters, key=len, reverse=True)[:2]
        v_top = sorted(v_clusters, key=len, reverse=True)[:2]
        print(f"    h_clusters (top2): {[(min(c),max(c),len(c)) for c in h_top]}")
        print(f"    v_clusters (top2): {[(min(c),max(c),len(c)) for c in v_top]}")
