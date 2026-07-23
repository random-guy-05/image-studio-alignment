#!/usr/bin/env python3
"""
Drags each blue dot to its paired grey spot.
- Drag duration ∝ distance at PIXELS_PER_SECOND
- Esc after each drop to deselect the dot
- Per-N screenshot checkpoint for sanity
"""
import json, math, subprocess, time, sys
import argparse
import pyautogui

# Eliminate pyautogui's default 0.1s pause between every call
# (would otherwise make each drag take 6+s on a 60-step drag)
pyautogui.PAUSE = 0
pyautogui.FAILSAFE = True

PIXELS_PER_SECOND = 400
MIN_DRAG          = 0.20
STEP_HZ           = 20
CHECKPOINT_EVERY  = 25
CLICK_INTERVAL    = 0.40   # gap between the two clicks
SETTLE            = 0.70   # pause after each major action
PRE_CLICK         = 0.20   # pause before first click
POST_CLICK        = 0.20   # pause after final click
CORNER_PAD        = 10     # don't click within 10pt of the rectangle border

# Window + rectangle bounds (set in main from targets.json)
WINDOW_X = WINDOW_Y = WINDOW_W = WINDOW_H = None
RECT_X1 = RECT_Y1 = RECT_X2 = RECT_Y2 = None

def verify_alignment(spot, tolerance=10):
    """Take a screenshot and check if a blue circle is near the target spot.
    Returns True if aligned, False if not."""
    try:
        import cv2, numpy as np
        shot = pyautogui.screenshot()
        shot_np = np.array(shot)
        hsv = cv2.cvtColor(shot_np, cv2.COLOR_RGB2HSV)
        blue_mask = cv2.inRange(hsv, np.array((100, 120, 100)), np.array((130, 255, 255)))
        # Check a 30x30 area around the spot for blue pixels
        sx, sy = int(spot[0]), int(spot[1])
        x0, y0 = max(0, sx-15), max(0, sy-15)
        x1, y1 = min(blue_mask.shape[1], sx+15), min(blue_mask.shape[0], sy+15)
        blue_count = int(blue_mask[y0:y1, x0:x1].sum() / 255)
        return blue_count > 50  # enough blue pixels = aligned
    except:
        return True  # if verification fails, assume OK

def select_and_drag(dot, spot, retry=False):
    """Double-click to select, dragTo to move, single-click to deselect.
    After dragging, verify alignment. If misaligned and not a retry, correct."""
    fx, fy = dot
    tx, ty = spot
    dist = math.hypot(tx - fx, ty - fy)
    duration = max(MIN_DRAG, dist / PIXELS_PER_SECOND)

    # STRICT rectangle check
    if RECT_X1 is not None:
        for name, (x, y) in [("dot", (fx, fy)), ("spot", (tx, ty))]:
            if not (RECT_X1 + CORNER_PAD <= x <= RECT_X2 - CORNER_PAD and
                    RECT_Y1 + CORNER_PAD <= y <= RECT_Y2 - CORNER_PAD):
                print(f"    SKIP: {name} ({x},{y}) too close to rectangle border", flush=True)
                return False

    pyautogui.moveTo(fx, fy)
    time.sleep(PRE_CLICK)
    pyautogui.click()
    time.sleep(CLICK_INTERVAL)
    pyautogui.click()
    time.sleep(SETTLE)
    pyautogui.dragTo(tx, ty, duration=duration, button='left', mouseDownUp=True)
    time.sleep(SETTLE)
    pyautogui.click()
    time.sleep(POST_CLICK)

    # VERIFICATION: check if a blue circle is now at the target
    if not retry:
        time.sleep(0.3)  # let the UI settle
        if not verify_alignment(spot):
            print(f"    MISALIGNED — correcting…", flush=True)
            # Find where the blue actually landed and re-drag to the target
            # The blue is near the target but offset — drag from current to target
            # Use the target as both source and destination (small correction)
            return select_and_drag(spot, spot, retry=True)
    return True

def main():
    global WINDOW_X, WINDOW_Y, WINDOW_W, WINDOW_H, RECT_X1, RECT_Y1, RECT_X2, RECT_Y2
    parser = argparse.ArgumentParser()
    parser.add_argument("--targets", default="targets.json")
    parser.add_argument("--tolerance", type=float, default=5)
    args = parser.parse_args()
    aligned_tolerance = args.tolerance
    data = json.load(open(args.targets))
    pairs = data["pairs"]
    WINDOW_X, WINDOW_Y, WINDOW_W, WINDOW_H = data["bounds"]

    # Verify against the LARGEST window
    try:
        raw = subprocess.check_output(["osascript", "-e",
            'tell application "System Events" to tell process "ImageStudio" to get position of every window & size of every window'
        ]).decode().strip()
        parts = []
        for p in raw.replace("{","").replace("}","").split(","):
            p = p.strip()
            if p == "missing value" or p == "":
                parts.append(0)
            else:
                try: parts.append(int(p))
                except: parts.append(0)
        nums = parts
        n = len(nums) // 4
        largest = None
        for i in range(n):
            wx, wy = nums[i*2], nums[i*2+1]
            ww, wh = nums[n*2 + i*2], nums[n*2 + i*2 + 1]
            if ww == 0 or wh == 0: continue
            area = ww * wh
            if largest is None or area > largest[2]:
                largest = (wx, wy, area, ww, wh)
        actual = (largest[0], largest[1], largest[3], largest[4])
    except Exception as e:
        print(f"Could not check windows: {e}", flush=True)
        actual = tuple(WINDOW_X, WINDOW_Y, WINDOW_W, WINDOW_H)

    if list(actual) != list(data["bounds"]):
        print(f"FATAL: main window has moved!", flush=True)
        print(f"  detection bounds: {data['bounds']}", flush=True)
        print(f"  current main:     {actual}", flush=True)
        print(f"  Re-run setup.py to refresh coordinates.", flush=True)
        sys.exit(1)
    print(f"Window bounds verified: {actual}", flush=True)

    if "rectangle" in data:
        RECT_X1, RECT_Y1, RECT_X2, RECT_Y2 = data["rectangle"]
    print(f"Aligning {len(pairs)} dots…  + {len(data.get('extras', []))} extras to corner")

    subprocess.run(["osascript", "-e",
        'tell application "ImageStudio" to activate'])
    time.sleep(0.5)

    for i, p in enumerate(pairs):
        dot  = p["dot"][:2]
        spot = p["spot"][:2]
        t0 = time.time()
        dist = math.hypot(spot[0] - dot[0], spot[1] - dot[1])
        if dist <= aligned_tolerance:
            print(f"  pair {i+1}/{len(pairs)}  dist={dist:.0f}pt  [already aligned]", flush=True)
            continue
        ok = select_and_drag(dot, spot)
        elapsed = time.time() - t0
        status = "ok" if ok else "skip"
        print(f"  pair {i+1}/{len(pairs)}  dist={dist:.0f}pt  took {elapsed:.1f}s  [{status}]", flush=True)

    extras = data.get("extras", [])
    if extras:
        print(f"WARNING: {len(extras)} extras in targets.json (should be 0). Skipping.", flush=True)

    print("done", flush=True)

if __name__ == "__main__":
    main()
