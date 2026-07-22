"""Cluster corner pixels and find the actual rectangle (not the screen edges)."""
import cv2, numpy as np
img = cv2.imread("/tmp/dots.png")
H, W = img.shape[:2]
print(f"Image: {W}x{H}")
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
blue_mask = cv2.inRange(hsv, np.array((100, 120, 100)), np.array((130, 255, 255)))

# Build h-run and v-run masks (excluding the very edges of the image)
EDGE = 50  # ignore pixels within 50px of the image edge
h_mask = np.zeros_like(blue_mask)
for y in range(EDGE, H-EDGE):
    row = blue_mask[y] > 0
    if not row.any(): continue
    padded = np.concatenate(([False], row, [False]))
    diffs = np.diff(padded.astype(int))
    starts = np.where(diffs == 1)[0]; ends = np.where(diffs == -1)[0]
    for s, e in zip(starts, ends):
        if e - s > 200: h_mask[y, s:e] = 255

v_mask = np.zeros_like(blue_mask)
for x in range(EDGE, W-EDGE):
    col = blue_mask[:, x] > 0
    if not col.any(): continue
    padded = np.concatenate(([False], col, [False]))
    diffs = np.diff(padded.astype(int))
    starts = np.where(diffs == 1)[0]; ends = np.where(diffs == -1)[0]
    for s, e in zip(starts, ends):
        if e - s > 100: v_mask[s:e, x] = 255

corners = cv2.bitwise_and(h_mask, v_mask)
corner_count = int((corners > 0).sum())
print(f"Corner pixels (excluding edges): {corner_count}")

if corner_count == 0:
    print("No corners found!"); exit()

ys, xs = np.where(corners > 0)
# Cluster corner pixels: group by (y//20, x//20)
from collections import defaultdict
clusters = defaultdict(list)
for y, x in zip(ys, xs):
    clusters[(y//20, x//20)].append((y, x))

print(f"\nCorner clusters ({len(clusters)}):")
for key, pts in sorted(clusters.items()):
    cy = sum(p[0] for p in pts) / len(pts)
    cx = sum(p[1] for p in pts) / len(pts)
    print(f"  cluster ({key[0]},{key[1]}): {len(pts)} pts  center=({cx:.0f},{cy:.0f})")

# Find the 4 clusters that form a rectangle of reasonable size
# (width 300-1000, height 150-500)
cluster_centers = [(sum(p[1] for p in pts)/len(pts), sum(p[0] for p in pts)/len(pts))
                   for pts in clusters.values()]
# Sort by y, then x
cluster_centers.sort()
print(f"\nCluster centers (sorted): {[(int(x),int(y)) for x,y in cluster_centers]}")

# The rectangle: find the tightest group of 4 clusters that form a rectangle
# Simple approach: the topmost 2 and bottommost 2 clusters
if len(cluster_centers) >= 4:
    # Group by y (top vs bottom)
    ys_sorted = sorted(set(int(y//50) for x, y in cluster_centers))
    if len(ys_sorted) >= 2:
        top_y = ys_sorted[0]
        bot_y = ys_sorted[-1]
        top_clusters = [(x,y) for x,y in cluster_centers if int(y//50) == top_y]
        bot_clusters = [(x,y) for x,y in cluster_centers if int(y//50) == bot_y]
        if top_clusters and bot_clusters:
            rect_top = min(y for x,y in top_clusters)
            rect_bot = max(y for x,y in bot_clusters)
            rect_left = min(x for x,y in top_clusters + bot_clusters)
            rect_right = max(x for x,y in top_clusters + bot_clusters)
            w = rect_right - rect_left
            h = rect_bot - rect_top
            print(f"\nRectangle: x=[{int(rect_left)},{int(rect_right)}]  y=[{int(rect_top)},{int(rect_bot)}]  ({int(w)}x{int(h)})")
            if 300 <= w <= 1000 and 150 <= h <= 500:
                print("  ✓ Reasonable size!")
            else:
                print(f"  ✗ Size out of range (need 300-1000 x 150-500)")
