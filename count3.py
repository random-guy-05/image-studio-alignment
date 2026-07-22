import json
d = json.load(open("/Users/admin/opencode-imagestudio/targets.json"))
print("pairs remaining:", len(d["pairs"]))
print("extras remaining:", len(d.get("extras", [])))
