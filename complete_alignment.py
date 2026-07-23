#!/usr/bin/env python3
"""Use verifier output to align only centers that still need correction."""
import argparse
import json
import subprocess
import sys
from pathlib import Path

from verify_alignment import verify

RESUME_TARGETS = "resume_targets.json"
ALIGN_SCRIPT = str(Path(__file__).resolve().parent / "align.py")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tolerance", type=float, default=10)
    args = parser.parse_args()
    report = verify(args.tolerance)
    repairs = report["repairs"]
    if not repairs:
        print("Nothing to repair.")
        return

    output = {
        "bounds": report["bounds"],
        "rectangle": json.load(open("targets.json"))["rectangle"],
        "pairs": [{"dot": item["blue"], "spot": item["target"]} for item in repairs],
        "extras": [],
    }
    with open(RESUME_TARGETS, "w") as f:
        json.dump(output, f, indent=2)
    print(f"Repairing {len(repairs)} centers")
    subprocess.run([sys.executable, ALIGN_SCRIPT, "--targets", RESUME_TARGETS], check=True)
    verify(args.tolerance)


if __name__ == "__main__":
    main()
