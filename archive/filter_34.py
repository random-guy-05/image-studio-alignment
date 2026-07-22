"""Filter the 34 pairs to remove outliers (>120) and show what we're about to drag."""
import json, math
data = json.load(open("/Users/admin/opencode-imagestudio/targets.json"))
pairs = data["pairs"]
print(f"Total: {len(pairs)}")
dists = [math.hypot(p['spot'][0]-p['dot'][0], p['spot'][1]-p['dot'][1]) for p in pairs]
print(f"Distance: min={min(dists):.0f} max={max(dists):.0f} avg={sum(dists)/len(dists):.0f}")
print(f"  >50: {sum(1 for d in dists if d>50)}  >80: {sum(1 for d in dists if d>80)}  >120: {sum(1 for d in dists if d>120)}")
filtered = [p for p in pairs if math.hypot(p['spot'][0]-p['dot'][0], p['spot'][1]-p['dot'][1]) <= 120]
print(f"\nFiltered to {len(filtered)} pairs (removed {len(pairs)-len(filtered)} outliers > 120)")
data["pairs"] = filtered
with open("/Users/admin/opencode-imagestudio/targets.json", "w") as f:
    json.dump(data, f, indent=2)
print("Saved targets.json")
