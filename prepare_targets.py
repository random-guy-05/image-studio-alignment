#!/usr/bin/env python3
"""Pair the current blue outlines with the definitive modeled data positions."""
import json
import math
import sys

import cv2
import numpy as np
from scipy.optimize import linear_sum_assignment
from platform_utils import activate_window, capture_fullscreen, get_largest_window

PREDICTED_PATH = "predicted_positions.json"
TARGETS_PATH = "targets.json"
BLUE_CAPTURE = "/tmp/blues_full.png"
EXPECTED_BLUE_COUNT = 240
BLUE_COUNT_TOLERANCE = 5


def detect_blue_centers(image, scale):
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
        minDist=round(15 * scale),
        param1=80,
        param2=30,
        minRadius=round(6 * scale),
        maxRadius=round(18 * scale),
    )
    if circles is None:
        return []
    return [(int(round(x)), int(round(y)), int(round(r))) for x, y, r in circles[0]]


def main():
    with open(PREDICTED_PATH) as f:
        prediction = json.load(f)

    positions = [tuple(point) for point in prediction["positions"]]
    rect_left, rect_top, rect_right, rect_bottom = prediction["rectangle"]
    prediction_scale_x, prediction_scale_y = prediction.get("scale", [1.0, 1.0])
    pixel_positions = [(round(x * prediction_scale_x), round(y * prediction_scale_y)) for x, y in positions]
    pixel_rect = (
        round(rect_left * prediction_scale_x),
        round(rect_top * prediction_scale_y),
        round(rect_right * prediction_scale_x),
        round(rect_bottom * prediction_scale_y),
    )
    wx, wy, ww, wh = get_largest_window()

    activate_window()
    capture_fullscreen(BLUE_CAPTURE)
    image = cv2.imread(BLUE_CAPTURE)
    if image is None:
        raise RuntimeError(f"Could not read {BLUE_CAPTURE}")

    scale_x = prediction_scale_x
    scale_y = prediction_scale_y
    scale = (scale_x + scale_y) / 2
    local_blues = detect_blue_centers(image, scale)
    blues = [
        (x, y, r)
        for x, y, r in local_blues
        if pixel_rect[0] < x < pixel_rect[2] and pixel_rect[1] < y < pixel_rect[3]
    ]
    if not blues:
        raise RuntimeError("No blue outlines detected inside the data rectangle")
    resume = "--resume" in sys.argv
    if not resume and not EXPECTED_BLUE_COUNT - BLUE_COUNT_TOLERANCE <= len(blues) <= EXPECTED_BLUE_COUNT + BLUE_COUNT_TOLERANCE:
        raise RuntimeError(
            f"Expected {EXPECTED_BLUE_COUNT} +/- {BLUE_COUNT_TOLERANCE} blue outlines, "
            f"detected {len(blues)}; refusing to prepare drags"
        )
    if resume and len(blues) > EXPECTED_BLUE_COUNT:
        raise RuntimeError(f"Resume detected {len(blues)} blue outlines; refusing more than {EXPECTED_BLUE_COUNT}")
    if len(blues) > len(positions):
        raise RuntimeError(f"Detected {len(blues)} blue outlines but only {len(positions)} targets exist")

    print(f"\n{'='*60}")
    print(f"  BLUE OUTLINES DETECTED: {len(blues)}  (target: {len(positions)})")
    print(f"{'='*60}\n")

    # Every predicted position is definitive. Match each blue to a unique
    # target, without filtering targets based on screenshot darkness.
    cost = np.zeros((len(blues), len(pixel_positions)), dtype=float)
    for i, (bx, by, _) in enumerate(blues):
        for j, (tx, ty) in enumerate(pixel_positions):
            cost[i, j] = math.hypot(bx - tx, by - ty)
    rows, cols = linear_sum_assignment(cost)

    pairs = []
    for row, col in zip(rows, cols):
        bx, by, _ = blues[row]
        tx, ty = positions[col]
        pairs.append({
            "dot": [round(bx / scale_x), round(by / scale_y)],
            "spot": list(positions[col]),
        })
    pairs.sort(key=lambda pair: (pair["spot"][1], pair["spot"][0]))

    output = {
        "bounds": [wx, wy, ww, wh],
        "rectangle": [rect_left, rect_top, rect_right, rect_bottom],
        "pairs": pairs,
        "extras": [],
        "predicted_position_count": len(positions),
    }
    with open(TARGETS_PATH, "w") as f:
        json.dump(output, f, indent=2)

    distances = [math.hypot(p["dot"][0] - p["spot"][0], p["dot"][1] - p["spot"][1]) for p in pairs]
    print(f"Predicted target positions: {len(positions)}")
    print(f"Blue outlines: {len(blues)}")
    print(f"Pairs written: {len(pairs)}")
    print(f"Initial pairing distance: median={np.median(distances):.1f}px max={max(distances):.1f}px")
    print(f"Saved: {TARGETS_PATH}")


if __name__ == "__main__":
    main()
