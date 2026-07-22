"""Fine-tune to land on exactly 220."""
import cv2, numpy as np
import json, math

cap = cv2.imread("/tmp/imagestudio.png")
hsv = cv2.cvtColor(cap, cv2.COLOR_BGR2HSV)

# Try variations around p2=25 to land on 220
configs = [
    # (lo, hi, p2, minR, maxR)
    ((0, 0, 180), (180, 20, 240), 25, 10, 18),
    ((0, 0, 180), (180, 20, 240), 25, 11, 18),
    ((0, 0, 180), (180, 20, 240), 25, 10, 17),
    ((0, 0, 180), (180, 20, 240), 25, 9, 18),
    ((0, 0, 178), (180, 22, 242), 25, 10, 18),
    ((0, 0, 175), (180, 25, 245), 24, 10, 18),
    ((0, 0, 175), (180, 25, 245), 25, 10, 18),
    ((0, 0, 170), (180, 30, 250), 23, 10, 18),
    ((0, 0, 170), (180, 30, 250), 24, 10, 18),
    # And try slightly different minDist
]

for cfg in configs:
    lo, hi, p2, minR, maxR = cfg
    mask = cv2.inRange(hsv, np.array(lo), np.array(hi))
    blurred = cv2.GaussianBlur(mask, (5, 5), 1)
    c = cv2.HoughCircles(blurred, cv2.HOUGH_GRADIENT, dp=1, minDist=20,
                         param1=80, param2=p2, minRadius=minR, maxRadius=maxR)
    n = 0 if c is None else len(c[0])
    print(f"  {cfg}: {n}  (diff from 220: {abs(n-220)})")
