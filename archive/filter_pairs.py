"""Filter out bad pairings (distance > 200) from targets.json."""
import json, math
data = json.load(open("/Users/admin/opencode-imagestudio/targets.json"))
pairs = data["pairs"]
print(f"Total pairs: {len(pairs)}")
dists = [math.hypot(p['spot'][0]-p['dot'][0], p['spot'][1]-p['dot'][1]) for p in pairs]
print(f"Distance distribution:")
for threshold in [25, 50, 100, 150, 200, 300, 500]:
    n = sum(1 for d in dists if d > threshold)
    print(f"  > {threshold}: {n}")

# Filter out very bad ones (>200) to avoid misaligning real dots
filtered = [p for p in pairs if math.hypot(p['spot'][0]-p['dot'][0], p['spot'][1]-p['dot'][1]) <= 200]
print(f"\nFiltered: {len(pairs)} -> {len(filtered)} (removed {len(pairs)-len(filtered)} outliers)")
data["pairs"] = filtered
with open("/Users/admin/opencode-imagestudio/targets.json", "w") as f:
    json.dump(data, f, indent=2)
print("Updated targets.json")
