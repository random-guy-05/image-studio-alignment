"""Filter out outliers (distance > 80) — only keep tight pairings."""
import json, math
data = json.load(open("/Users/admin/opencode-imagestudio/targets.json"))
pairs = data["pairs"]
print(f"Total pairs: {len(pairs)}")
dists = [math.hypot(p['spot'][0]-p['dot'][0], p['spot'][1]-p['dot'][1]) for p in pairs]
print(f"Distance distribution:")
for t in [10, 25, 50, 80, 100, 150, 200]:
    n = sum(1 for d in dists if d > t)
    print(f"  > {t}: {n}")

# Keep only tight pairings (distance <= 80) — the 7 outliers are bad
filtered = [p for p in pairs if math.hypot(p['spot'][0]-p['dot'][0], p['spot'][1]-p['dot'][1]) <= 80]
removed = len(pairs) - len(filtered)
print(f"\nFiltered: {len(pairs)} -> {len(filtered)}  (removed {removed} outliers)")
data["pairs"] = filtered
with open("/Users/admin/opencode-imagestudio/targets.json", "w") as f:
    json.dump(data, f, indent=2)
print("Updated targets.json")
