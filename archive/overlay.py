"""Draw detected circles on the screenshot for sanity check."""
import json
import cv2

img = cv2.imread("/tmp/imagestudio.png")
data = json.load(open("/Users/admin/opencode-imagestudio/targets.json"))
bounds = data["bounds"]
scale = data["scale"]
pairs = data["pairs"]
ox, oy = bounds[0], bounds[1]

for i, p in enumerate(pairs):
    # Convert point coords back to physical pixel coords for drawing
    dx = int((p["dot"][0] - ox) * scale)
    dy = int((p["dot"][1] - oy) * scale)
    sx = int((p["spot"][0] - ox) * scale)
    sy = int((p["spot"][1] - oy) * scale)
    # Green for dot, red for spot
    cv2.circle(img, (dx, dy), 18, (0, 255, 0), 2)
    cv2.circle(img, (sx, sy), 18, (0, 0, 255), 2)
    # Index label
    if i < 5 or i > len(pairs) - 5:
        cv2.putText(img, str(i), (dx + 20, dy - 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

cv2.imwrite("/tmp/overlay.png", img)
print(f"Saved /tmp/overlay.png  with {len(pairs)} pairs marked")
print(f"First pair (points):  dot={pairs[0]['dot']}  spot={pairs[0]['spot']}")
print(f"Last pair (points):   dot={pairs[-1]['dot']}  spot={pairs[-1]['spot']}")
# Distance stats
import math
dists = [math.hypot(p['spot'][0]-p['dot'][0], p['spot'][1]-p['dot'][1]) for p in pairs]
print(f"Distance stats (points): min={min(dists):.0f}  max={max(dists):.0f}  avg={sum(dists)/len(dists):.0f}")
print(f"  any suspiciously large (>200 pts): {sum(1 for d in dists if d > 200)}")
