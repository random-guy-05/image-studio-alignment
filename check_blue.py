"""Check what blue features are in the new screenshot."""
import cv2, numpy as np
img = cv2.imread("/tmp/dots.png")
H, W = img.shape[:2]
print(f"Image: {W}x{H}")
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
blue_mask = cv2.inRange(hsv, np.array((100, 120, 100)), np.array((130, 255, 255)))
print(f"Blue pixels: {int((blue_mask>0).sum())}")

# Where are the blue pixels? Show distribution
rows_with_blue = np.where(blue_mask.sum(axis=1) > 0)[0]
cols_with_blue = np.where(blue_mask.sum(axis=0) > 0)[0]
print(f"Rows with blue: {len(rows_with_blue)}  range [{rows_with_blue.min()},{rows_with_blue.max()}]")
print(f"Cols with blue: {len(cols_with_blue)}  range [{cols_with_blue.min()},{cols_with_blue.max()}]")

# Show blue pixel density per row (top 20)
row_density = blue_mask.sum(axis=1) / 255
top_rows = np.argsort(row_density)[-20:][::-1]
print(f"\nTop 20 rows by blue density:")
for y in sorted(top_rows):
    print(f"  row {y}: {int(row_density[y])} blue pixels")

# Show blue pixel density per col (top 20)
col_density = blue_mask.sum(axis=0) / 255
top_cols = np.argsort(col_density)[-20:][::-1]
print(f"\nTop 20 cols by blue density:")
for x in sorted(top_cols):
    print(f"  col {x}: {int(col_density[x])} blue pixels")
