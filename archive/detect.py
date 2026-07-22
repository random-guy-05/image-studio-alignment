#!/usr/bin/env python3
"""
Detects blue-outlined circles and grey/black spots in the ImageStudio window
using HoughCircles (handles ring shapes + Retina pixel density).

Pairing uses the Hungarian algorithm (scipy.optimize.linear_sum_assignment)
for globally optimal assignment — no two blues to the same spot, no
over-moving.

Writes targets.json with paired coordinates in screen POINTS.
"""
import json, math, subprocess, sys
import cv2
import numpy as np
from scipy.optimize import linear_sum_assignment

# === HSV ranges — match your specific colors ===
BLUE_HSV = ((100, 120, 100), (130, 255, 255))   # blue ring outline
GREY_LIGHT_HSV = ((0, 0, 180), (180, 20, 240))  # VERY LIGHT grey spots
GREY_BLACK_HSV = ((0, 0,   0), (180, 60,  60))  # BLACK spots (V<60, S<60)

# HoughCircle params (calibrated for Retina 2x density)
HOUGH = dict(dp=1, minDist=20, param1=80, param2=15, minRadius=12, maxRadius=18)
HOUGH_LIGHT = dict(dp=1, minDist=20, param1=80, param2=25, minRadius=9, maxRadius=18)
HOUGH_BLACK = dict(dp=1, minDist=20, param1=80, param2=22, minRadius=9, maxRadius=18)

def window_bounds():
    out = subprocess.check_output(["osascript", "-e",
        'tell application "System Events" to tell process "ImageStudio" '
        'to get position of front window & size of front window'
    ]).decode().strip()
    nums = [int(x.strip()) for x in out.replace("{","").replace("}","").split(",")]
    return nums[0], nums[1], nums[2], nums[3]

def capture(bounds, path):
    x, y, w, h = bounds
    subprocess.run(["screencapture", "-R", f"{x},{y},{w},{h}", path], check=True)

def hough_circles(mask, params):
    blurred = cv2.GaussianBlur(mask, (5, 5), 1)
    circles = cv2.HoughCircles(blurred, cv2.HOUGH_GRADIENT, **params)
    if circles is None:
        return []
    return [(int(c[0]), int(c[1]), int(c[2])) for c in circles[0]]

def dedup(points, min_separation=15):
    """Remove points that are too close together (keep one per cluster)."""
    if not points:
        return []
    kept = []
    for p in points:
        too_close = False
        for q in kept:
            if math.hypot(p[0]-q[0], p[1]-q[1]) < min_separation:
                too_close = True
                break
        if not too_close:
            kept.append(p)
    return kept

def main():
    bounds = window_bounds()
    img_path = "/tmp/imagestudio.png"
    capture(bounds, img_path)
    img = cv2.imread(img_path)
    H, W = img.shape[:2]
    scale_x = W / bounds[2]
    scale_y = H / bounds[3]
    print(f"Window (points): {bounds}")
    print(f"Captured (phys px): {W}x{H}  scale={scale_x:.2f}x")

    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    blue_mask  = cv2.inRange(hsv, np.array(BLUE_HSV[0]),     np.array(BLUE_HSV[1]))
    grey_light = cv2.inRange(hsv, np.array(GREY_LIGHT_HSV[0]), np.array(GREY_LIGHT_HSV[1]))
    grey_black = cv2.inRange(hsv, np.array(GREY_BLACK_HSV[0]), np.array(GREY_BLACK_HSV[1]))

    blue_pts  = hough_circles(blue_mask,  HOUGH)
    light_pts = hough_circles(grey_light, HOUGH_LIGHT)
    black_pts = hough_circles(grey_black, HOUGH_BLACK)

    # Combine and dedup grey spots (light + black) — they may overlap
    grey_pts = dedup(light_pts + black_pts, min_separation=15)

    print(f"blue circles:    {len(blue_pts)}")
    print(f"light grey pts:  {len(light_pts)}")
    print(f"black pts:       {len(black_pts)}")
    print(f"grey (deduped):  {len(grey_pts)}")
    if blue_pts:
        print(f"  first blue (phys px):  {blue_pts[0]}")
    if grey_pts:
        print(f"  first grey (phys px):  {grey_pts[0]}")

    if not blue_pts or not grey_pts:
        print("ERROR: no circles detected", file=sys.stderr)
        sys.exit(1)

    # Convert to point coordinates
    ox, oy = bounds[0], bounds[1]
    blue_in_pts  = [(ox + x / scale_x, oy + y / scale_y) for x, y, _ in blue_pts]
    grey_in_pts  = [(ox + x / scale_x, oy + y / scale_y) for x, y, _ in grey_pts]

    # Hungarian assignment: cost = euclidean distance
    # linear_sum_assignment handles rectangular matrices; unmatched rows are dropped
    n_blue = len(blue_in_pts)
    n_grey = len(grey_in_pts)
    cost = np.full((n_blue, n_grey), 1e6, dtype=np.float64)
    for i, (bx, by) in enumerate(blue_in_pts):
        for j, (gx, gy) in enumerate(grey_in_pts):
            d = math.hypot(bx - gx, by - gy)
            cost[i, j] = d

    row_idx, col_idx = linear_sum_assignment(cost)

    # Build pairs in X-sorted order (stable, easier to debug)
    pairs_raw = []
    for r, c in zip(row_idx, col_idx):
        if cost[r, c] > 5000:    # unmatched (filled with 1e6)
            continue
        pairs_raw.append((blue_in_pts[r], grey_in_pts[c], cost[r, c]))

    # Sort by blue X for consistent ordering
    pairs_raw.sort(key=lambda p: p[0][0])
    pairs = [{"dot": [round(p[0][0]), round(p[0][1])],
              "spot": [round(p[1][0]), round(p[1][1])]}
             for p in pairs_raw]

    if not pairs:
        print("ERROR: no valid pairs after Hungarian assignment", file=sys.stderr)
        sys.exit(1)

    with open("targets.json", "w") as f:
        json.dump({"bounds": list(bounds), "scale": scale_x, "pairs": pairs}, f, indent=2)
    print(f"Wrote {len(pairs)} pairs to targets.json (Hungarian assignment)")
    dists = [p[2] for p in pairs_raw]
    if dists:
        print(f"Distance stats (points): min={min(dists):.0f}  max={max(dists):.0f}  avg={sum(dists)/len(dists):.0f}")
        print(f"  >50 pts: {sum(1 for d in dists if d > 50)}  >100: {sum(1 for d in dists if d > 100)}  >200: {sum(1 for d in dists if d > 200)}")

if __name__ == "__main__":
    main()
