"""Run ONE batch: take first 5 pairs, run align, remove them from targets.json.
Then report progress."""
import json, subprocess, time, sys

targets_file = "/Users/admin/opencode-imagestudio/targets.json"
BATCH_SIZE = 5

data = json.load(open(targets_file))
all_pairs = data["pairs"]
batch = all_pairs[:BATCH_SIZE]
remaining = all_pairs[BATCH_SIZE:]
print(f"Total: {len(all_pairs)}  Batch: {len(batch)}  Remaining after: {len(remaining)}")

if not batch:
    print("DONE — no more pairs", flush=True)
    sys.exit(0)

# Write just this batch to targets.json
data["pairs"] = batch
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
elapsed = time.time() - t0
print(f"\n--- align.py stdout ({elapsed:.1f}s) ---")
print(result.stdout)
if result.stderr:
    print(f"--- stderr ---")
    print(result.stderr[-500:])

# Put the remaining pairs back (in case align modified the file)
data = json.load(open(targets_file))
# data["pairs"] is now empty (align read it all). Restore the remaining.
data["pairs"] = remaining
with open(targets_file, "w") as f:
    json.dump(data, f, indent=2)
print(f"\nRestored {len(remaining)} remaining pairs to targets.json")
print(f"Progress: {len(batch)} done, {len(remaining)} left")
