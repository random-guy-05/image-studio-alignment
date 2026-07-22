import cv2, numpy as np
img = cv2.imread("/tmp/v3.png")
print(f"Capture size: {img.shape[1]}x{img.shape[0]}")
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
blue_mask = cv2.inRange(hsv, np.array((100, 120, 100)), np.array((130, 255, 255)))
print(f"blue pixels: {int((blue_mask>0).sum())}")
# Row counts
row_blue = blue_mask.sum(axis=1) / 255
threshold = row_blue.max() * 0.3 if row_blue.max() > 0 else 100
print(f"max blue in a row: {int(row_blue.max())}  threshold: {int(threshold)}")
# Find ALL rows with significant blue
significant = np.where(row_blue > 50)[0]
print(f"rows with >50 blue: {len(significant)}")
if len(significant) > 0:
    print(f"  first 10: {significant[:10]}")
    print(f"  last 10:  {significant[-10:]}")
# All HoughCircles on blue (no radius restriction)
bb = cv2.GaussianBlur(blue_mask, (5, 5), 1)
c = cv2.HoughCircles(bb, cv2.HOUGH_GRADIENT, dp=1, minDist=15, param1=80, param2=10, minRadius=5, maxRadius=30)
n = 0 if c is None else len(c[0])
print(f"\nblue Hough (loose): {n}")
