#!/usr/bin/env python3
"""Pair the current blue outlines with the definitive modeled data positions."""
import json
import math
import subprocess
import time

import cv2
import numpy as np
from scipy.optimize import linear_sum_assignment

PREDICTED_PATH = "predicted_positions.json"
TARGETS_PATH = "targets.json"
BLUE_CAPTURE = "/tmp/blues.png"


def get_main_window():
    raw = subprocess.check_output([
        "osascript", "-e",
        "tell application \"System Events\" to tell process \"ImageStudio\" to get position of every window & size of every window",
    ]).decode().strip()
    parts = []
    for value in raw.replace("{", "").replace("}", "").split(","):
        value = value.strip()
        try:
            parts.append(int(value))
        except ValueError:
            parts.append(0)
    count = len(parts) // 4
    windows = []
    for i in range(count):
        x, y = parts[i * 2], parts[i * 2 + 1]
        w, h = parts[count * 2 + i * 2], parts[count * 2 + i * 2 + 1]
        if w and h:
            windows.append((x, y, w, h, w * h))
    if not windows:
        raise RuntimeError("Could not find an ImageStudio window")
    windows.sort(key=lambda item: -item[4])
    return windows[0][:4]


def detect_blue_centers(image):
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(
        hsv,
        np.array((100, 120, 100)),
        np.array((130, 255, 255)),
    )
    circles = cv2.HoughCircles(
        cv2.GaussianBlur(mask, (5, 5), 1),
        cv2.HOUGH_GRADIENT,
        dp=1,
        minDist=15,
        param1=80,
        param2=30,
        minRadius=6,
        maxRadius=18,
    )
    if circles is None:
        return []
    return [(int(round(x)), int(round(y)), int(round(r))) for x, y, r in circles[0]]


def main():
    with open(PREDICTED_PATH) as f:
        prediction = json.load(f)

    positions = [tuple(point) for point in prediction["positions"]]
    rect_left, rect_top, rect_right, rect_bottom = prediction["rectangle"]
    wx, wy, ww, wh = get_main_window()

    subprocess.run(["osascript", "-e", "tell application \"ImageStudio\" to activate"], check=True)
    time.sleep(0.4)
    subprocess.run([
        "screencapture", "-R", f"{wx},{wy},{ww},{wh}", BLUE_CAPTURE,
    ], check=True)
    image = cv2.imread(BLUE_CAPTURE)
    if image is None:
        raise RuntimeError(f"Could not read {BLUE_CAPTURE}")

    scale_x = image.shape[1] / ww
    scale_y = image.shape[0] / wh
    detection_image = cv2.resize(image, (ww, wh), interpolation=cv2.INTER_AREA)
    local_blues = detect_blue_centers(detection_image)
    blues = [
        (round(wx + x), round(wy + y), r)
        for x, y, r in local_blues
        if rect_left < wx + x < rect_right and rect_top < wy + y < rect_bottom
    ]
    if not blues:
        raise RuntimeError("No blue outlines detected inside the data rectangle")
    if len(blues) > len(positions):
        raise RuntimeError(f"Detected {len(blues)} blue outlines but only {len(positions)} targets exist")

    # Every predicted position is definitive. Match each blue to a unique
    # target, without filtering targets based on screenshot darkness.
    cost = np.zeros((len(blues), len(positions)), dtype=float)
    for i, (bx, by, _) in enumerate(blues):
        for j, (tx, ty) in enumerate(positions):
            cost[i, j] = math.hypot(bx - tx, by - ty)
    rows, cols = linear_sum_assignment(cost)

    pairs = []
    for row, col in zip(rows, cols):
        bx, by, _ = blues[row]
        tx, ty = positions[col]
        pairs.append({"dot": [bx, by], "spot": [tx, ty]})
    pairs.sort(key=lambda pair: (pair["spot"][1], pair["spot"][0]))

    output = {
        "bounds": [wx, wy, ww, wh],
        "rectangle": prediction["rectangle"],
        "pairs": pairs,
        "extras": [],
        "predicted_position_count": len(positions),
    }
    with open(TARGETS_PATH, "w") as f:
        json.dump(output, f, indent=2)

    preview = image.copy()
    for bx, by, _ in blues:
        x = round((bx - wx) * scale_x)
        y = round((by - wy) * scale_y)
        cv2.circle(preview, (x, y), 10, (0, 0, 255), 2)
    for tx, ty in positions:
        x = round((tx - wx) * scale_x)
        y = round((ty - wy) * scale_y)
        cv2.circle(preview, (x, y), 4, (0, 255, 0), 1)
    cv2.imwrite("screenshots/blue_target_overlay.png", preview)

    distances = [math.hypot(p["dot"][0] - p["spot"][0], p["dot"][1] - p["spot"][1]) for p in pairs]
    print(f"Predicted target positions: {len(positions)}")
    print(f"Blue outlines: {len(blues)}")
    print(f"Pairs written: {len(pairs)}")
    print(f"Initial pairing distance: median={np.median(distances):.1f}px max={max(distances):.1f}px")
    print(f"Saved: {TARGETS_PATH}")
    print("Preview: screenshots/blue_target_overlay.png")


if __name__ == "__main__":
    main()
