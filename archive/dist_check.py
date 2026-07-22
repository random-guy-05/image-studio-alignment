"""Check spatial distribution of blue vs grey detections."""
import json
data = json.load(open("/Users/admin/opencode-imagestudio/targets.json"))
pairs = data["pairs"]

dot_xs = [p["dot"][0] for p in pairs]
dot_ys = [p["dot"][1] for p in pairs]
spot_xs = [p["spot"][0] for p in pairs]
spot_ys = [p["spot"][1] for p in pairs]

print(f"  DOTS  X: min={min(dot_xs)} max={max(dot_xs)} avg={sum(dot_xs)/len(dot_xs):.0f}")
print(f"  DOTS  Y: min={min(dot_ys)} max={max(dot_ys)} avg={sum(dot_ys)/len(dot_ys):.0f}")
print(f"  SPOTS X: min={min(spot_xs)} max={max(spot_xs)} avg={sum(spot_xs)/len(spot_xs):.0f}")
print(f"  SPOTS Y: min={min(spot_ys)} max={max(spot_ys)} avg={sum(spot_ys)/len(spot_ys):.0f}")

# Check Y distributions by bucket
print("\nY-distribution (DOTS):")
buckets = [0]*8
for y in dot_ys:
    buckets[min(7, y//100)] += 1
for i, c in enumerate(buckets):
    print(f"  Y {i*100}-{(i+1)*100}: {c}")
print("Y-distribution (SPOTS):")
buckets = [0]*8
for y in spot_ys:
    buckets[min(7, y//100)] += 1
for i, c in enumerate(buckets):
    print(f"  Y {i*100}-{(i+1)*100}: {c}")

# Quick check: for first 10 pairs, what's the actual X order
print("\nFirst 10 pairs (X-sorted):")
for i, p in enumerate(pairs[:10]):
    print(f"  {i}: dot=({p['dot'][0]},{p['dot'][1]})  spot=({p['spot'][0]},{p['spot'][1]})")
