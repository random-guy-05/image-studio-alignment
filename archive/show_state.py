import json
d = json.load(open("/Users/admin/opencode-imagestudio/targets.json"))
print("bounds:", d["bounds"])
print("rectangle:", d.get("rectangle"))
print("pairs:", len(d["pairs"]))
