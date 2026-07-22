"""Test select_and_drag function with 10 pairs to see if it hangs."""
import json, math, subprocess, time, sys
import pyautogui

pyautogui.PAUSE = 0
pyautogui.FAILSAFE = True

PIXELS_PER_SECOND = 500
MIN_DRAG = 0.15
CLICK_INTERVAL = 0.25
SETTLE = 0.40

def select_and_drag(dot, spot):
    fx, fy = dot
    tx, ty = spot
    dist = math.hypot(tx - fx, ty - fy)
    duration = max(MIN_DRAG, dist / PIXELS_PER_SECOND)
    pyautogui.moveTo(fx, fy)
    time.sleep(0.10)
    pyautogui.click()
    time.sleep(CLICK_INTERVAL)
    pyautogui.click()
    time.sleep(SETTLE)
    pyautogui.dragTo(tx, ty, duration=duration, button='left', mouseDownUp=True)
    time.sleep(SETTLE)
    pyautogui.click()
    time.sleep(0.10)

data = json.load(open("/Users/admin/opencode-imagestudio/targets.json"))
pairs = data["pairs"][:10]

subprocess.run(["osascript", "-e", 'tell application "ImageStudio" to activate'], check=True)
time.sleep(0.5)

t0 = time.time()
for i, p in enumerate(pairs):
    pt0 = time.time()
    select_and_drag(p["dot"], p["spot"])
    print(f"  pair {i+1:2d}/10  took {time.time()-pt0:.2f}s  total={time.time()-t0:.1f}s", flush=True)
print(f"\nDone in {time.time()-t0:.1f}s", flush=True)
