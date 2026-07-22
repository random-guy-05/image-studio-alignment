"""Run N batches in sequence."""
import sys, subprocess
N = int(sys.argv[1]) if len(sys.argv) > 1 else 5
for i in range(N):
    print(f"\n========== BATCH {i+1}/{N} ==========", flush=True)
    result = subprocess.run(
        ["python3", "-u", "/Users/admin/opencode-imagestudio/batch.py"],
        capture_output=True, text=True, timeout=120
    )
    # Show last few lines of stdout
    lines = result.stdout.strip().split("\n")
    for line in lines[-6:]:
        print(line, flush=True)
    if result.returncode != 0:
        print(f"BATCH FAILED: {result.returncode}", flush=True)
        print(result.stderr[-300:] if result.stderr else "", flush=True)
        break
print("\nDONE", flush=True)
