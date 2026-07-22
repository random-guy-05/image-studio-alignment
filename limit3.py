import json
data = json.load(open("/Users/admin/opencode-imagestudio/targets.json"))
data["pairs"] = data["pairs"][:3]
with open("/Users/admin/opencode-imagestudio/targets.json", "w") as f:
    json.dump(data, f, indent=2)
print(f"Limited to 3 pairs for test")
