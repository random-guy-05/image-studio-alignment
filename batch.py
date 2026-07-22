"""Run ONE batch: take first N pairs, run align, restore remaining."""
import json, subprocess, time, sys
targets_file = "/Users/admin/opencode-imagestudio/targets.json"
BATCH_SIZE = int(sys.argv[1]) if len(sys.argv) > 1 else 5

data = json.load(open(targets_file))
all_pairs = data["pairs"]
all_extras = data.get("extras", [])
batch = all_pairs[:BATCH_SIZE]
remaining = all_pairs[BATCH_SIZE:]
print(f"Total pairs: {len(all_pairs)}  Extras: {len(all_extras)}  Batch: {len(batch)}  Remaining: {len(remaining)}", flush=True)

if not batch and not all_extras:
    print("DONE — no more work", flush=True)
    sys.exit(0)

# Write just this batch
data["pairs"] = batch
data["extras"] = []
with open(targets_file, "w") as f:
    json.dump(data, f, indent=2)

# Activate
for _ in range(3):
    subprocess.run(["osascript", "-e", 'tell application "ImageStudio" to activate'], check=True)
    time.sleep(0.3)

# Run align
t0 = time.time()
result = subprocess.run(
    ["python3", "-u", "/Users/admin/opencode-imagestudio/align.py"],
    capture_output=True, text=True, timeout=120
)
print(f"--- align.py ({time.time()-t0:.1f}s) ---", flush=True)
print(result.stdout, flush=True)
if result.returncode != 0:
    print(f"FAILED: {result.returncode}", flush=True)
    if result.stderr:
        print(result.stderr[-500:], flush=True)

# Restore remaining
data = json.load(open(targets_file))
data["pairs"] = remaining
data["extras"] = all_extras
with open(targets_file, "w") as f:
    json.dump(data, f, indent=2)
print(f"Restored: {len(remaining)} pairs + {len(all_extras)} extras remaining", flush=True)
