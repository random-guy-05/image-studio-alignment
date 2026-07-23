#!/usr/bin/env python3
"""Verify every visible blue center against the definitive modeled targets."""
import argparse
import json
import math

import cv2
import numpy as np
from scipy.optimize import linear_sum_assignment

from prepare_targets import detect_blue_centers
from platform_utils import capture_fullscreen, get_largest_window

BLUE_CAPTURE = "/tmp/verify_blues_full.png"
REPORT_PATH = "verification.json"


def verify(tolerance=10):
    with open("predicted_positions.json") as f:
        prediction = json.load(f)
    targets = [tuple(point) for point in prediction["positions"]]
    scale_x, scale_y = prediction.get("scale", [1.0, 1.0])
    rect = prediction["rectangle"]
    pixel_rect = [round(rect[0] * scale_x), round(rect[1] * scale_y),
                  round(rect[2] * scale_x), round(rect[3] * scale_y)]
    try:
        wx, wy, ww, wh = get_largest_window()
    except Exception as exc:
        raise RuntimeError("Open ImageStudio with the blue outlines visible before verifying") from exc

    capture_fullscreen(BLUE_CAPTURE)
    image = cv2.imread(BLUE_CAPTURE)
    if image is None:
        raise RuntimeError(f"Could not read {BLUE_CAPTURE}")
    circles = detect_blue_centers(image, (scale_x + scale_y) / 2)
    blues = [
        (round(x / scale_x), round(y / scale_y))
        for x, y, _ in circles
        if pixel_rect[0] < x < pixel_rect[2] and pixel_rect[1] < y < pixel_rect[3]
    ]

    if blues and targets:
        cost = np.array([[math.hypot(bx - tx, by - ty) for tx, ty in targets]
                         for bx, by in blues])
        rows, cols = linear_sum_assignment(cost)
    else:
        cost = np.empty((0, 0))
        rows, cols = [], []

    matches = []
    matched_targets = set()
    repairs = []
    for row, col in zip(rows, cols):
        distance = float(cost[row, col])
        match = {
            "blue": list(blues[row]),
            "target": list(targets[col]),
            "distance": round(distance, 2),
            "aligned": distance <= tolerance,
        }
        matches.append(match)
        matched_targets.add(int(col))
        if distance > tolerance:
            repairs.append(match)

    missing = [list(targets[i]) for i in range(len(targets)) if i not in matched_targets]

    # Detect overlapping blue outlines (two blues assigned to nearby targets).
    overlaps = []
    for i in range(len(matches)):
        for j in range(i + 1, len(matches)):
            d = math.hypot(matches[i]["blue"][0] - matches[j]["blue"][0],
                           matches[i]["blue"][1] - matches[j]["blue"][1])
            if d < tolerance * 2:
                overlaps.append({"blue_a": matches[i]["blue"], "blue_b": matches[j]["blue"],
                                 "distance": round(d, 2)})

    report = {
        "tolerance": tolerance,
        "target_count": len(targets),
        "blue_count": len(blues),
        "matched_count": len(matches),
        "aligned_count": len(matches) - len(repairs),
        "misaligned_count": len(repairs),
        "missing_count": len(missing),
        "repairs": repairs,
        "missing_targets": missing,
        "overlaps": overlaps,
        "bounds": [wx, wy, ww, wh],
        "matches": matches,
    }
    with open(REPORT_PATH, "w") as f:
        json.dump(report, f, indent=2)
    print(f"Targets: {len(targets)}")
    print(f"Blue outlines: {len(blues)}")
    print(f"Aligned: {report['aligned_count']}")
    print(f"Misaligned: {report['misaligned_count']}")
    print(f"Missing: {report['missing_count']}")
    if overlaps:
        print(f"Overlaps: {len(overlaps)}")
    print(f"Saved: {REPORT_PATH}")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--tolerance", type=float, default=5)
    args = parser.parse_args()
    result = verify(args.tolerance)
    raise SystemExit(0 if result["misaligned_count"] == 0 and result["missing_count"] == 0 else 1)
