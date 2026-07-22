#!/usr/bin/env python3
"""Quick test: just 3 pairs with verbose timing."""
import json, math, subprocess, time, sys
import pyautogui

pyautogui.PAUSE = 0
pyautogui.FAILSAFE = True

data = json.load(open("/Users/admin/opencode-imagestudio/targets.json"))
pairs = data["pairs"][:3]

# Safety check
targets_bounds = data["bounds"]
out = subprocess.check_output(["osascript", "-e",
    'tell application "System Events" to tell process "ImageStudio" to get position of front window & size of front window'
]).decode().strip()
nums = [int(x.strip()) for x in out.replace("{","").replace("}","").split(",")]
cur = (nums[0], nums[1], nums[2], nums[3])
print(f"Window: {cur}  (targets: {targets_bounds})", flush=True)
if list(cur) != targets_bounds:
    print("MISMATCH — re-detect needed", flush=True)
    sys.exit(1)

subprocess.run(["osascript", "-e", 'tell application "ImageStudio" to activate'], check=True)
time.sleep(0.5)

CLICK_INTERVAL = 0.25
SETTLE = 0.40
MIN_DRAG = 0.15
PIXELS_PER_SECOND = 500

for i, p in enumerate(pairs):
    t0 = time.time()
    fx, fy = p["dot"]
    tx, ty = p["spot"]
    dist = math.hypot(tx-fx, ty-fy)
    duration = max(MIN_DRAG, dist / PIXELS_PER_SECOND)
    print(f"\n--- Pair {i}: dot ({fx},{fy}) → spot ({tx},{ty})  dist={dist:.0f}  dur={duration:.2f}s ---", flush=True)

    t = time.time()
    pyautogui.moveTo(fx, fy)
    print(f"  moveTo: {time.time()-t:.3f}s", flush=True)
    time.sleep(0.10)

    t = time.time()
    pyautogui.click()
    print(f"  click1: {time.time()-t:.3f}s", flush=True)
    time.sleep(CLICK_INTERVAL)

    t = time.time()
    pyautogui.click()
    print(f"  click2: {time.time()-t:.3f}s", flush=True)
    time.sleep(SETTLE)

    t = time.time()
    pyautogui.dragTo(tx, ty, duration=duration, button='left', mouseDownUp=True)
    print(f"  dragTo: {time.time()-t:.3f}s", flush=True)
    time.sleep(SETTLE)

    t = time.time()
    pyautogui.click()
    print(f"  click3: {time.time()-t:.3f}s", flush=True)
    time.sleep(0.10)

    print(f"  TOTAL: {time.time()-t0:.2f}s", flush=True)

print("\nDone.", flush=True)
