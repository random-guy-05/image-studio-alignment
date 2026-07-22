"""Run 15 pairs and see if per-pair time degrades."""
import json, math, subprocess, time
import pyautogui

pyautogui.PAUSE = 0
pyautogui.FAILSAFE = True

data = json.load(open("/Users/admin/opencode-imagestudio/targets.json"))
pairs = data["pairs"][:15]

# Safety check
out = subprocess.check_output(["osascript", "-e",
    'tell application "System Events" to tell process "ImageStudio" to get position of front window & size of front window'
]).decode().strip()
nums = [int(x.strip()) for x in out.replace("{","").replace("}","").split(",")]
cur = (nums[0], nums[1], nums[2], nums[3])
if list(cur) != data["bounds"]:
    print(f"WINDOW MISMATCH: {cur} vs {data['bounds']}", flush=True)
    raise SystemExit(1)

subprocess.run(["osascript", "-e", 'tell application "ImageStudio" to activate'], check=True)
time.sleep(0.5)

t_start = time.time()
for i, p in enumerate(pairs):
    fx, fy = p["dot"]
    tx, ty = p["spot"]
    dist = math.hypot(tx-fx, ty-fy)
    t0 = time.time()
    pyautogui.moveTo(fx, fy)
    time.sleep(0.10)
    pyautogui.click()
    time.sleep(0.25)
    pyautogui.click()
    time.sleep(0.40)
    pyautogui.dragTo(tx, ty, duration=max(0.15, dist/500), button='left', mouseDownUp=True)
    time.sleep(0.40)
    pyautogui.click()
    time.sleep(0.10)
    elapsed = time.time() - t0
    total = time.time() - t_start
    print(f"  pair {i+1:2d}/15  dist={dist:5.0f}pt  took {elapsed:5.2f}s  total={total:6.1f}s", flush=True)

print(f"\nAll 15 done in {time.time()-t_start:.1f}s", flush=True)
