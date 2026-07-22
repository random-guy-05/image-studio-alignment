import json, math
data = json.load(open("/Users/admin/opencode-imagestudio/targets.json"))
pairs = data["pairs"]
print(f"Total: {len(pairs)}")
dists = [math.hypot(p['spot'][0]-p['dot'][0], p['spot'][1]-p['dot'][1]) for p in pairs]
for t in [25, 50, 80, 100]:
    print(f"  > {t}: {sum(1 for d in dists if d > t)}")
filtered = [p for p in pairs if math.hypot(p['spot'][0]-p['dot'][0], p['spot'][1]-p['dot'][1]) <= 80]
print(f"Filtered: {len(pairs)} -> {len(filtered)}")
data["pairs"] = filtered
with open("/Users/admin/opencode-imagestudio/targets.json", "w") as f:
    json.dump(data, f, indent=2)
print("Saved.")
