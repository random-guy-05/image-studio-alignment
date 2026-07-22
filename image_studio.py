#!/usr/bin/env python3
"""Friendly command-line entry point for the ImageStudio workflow."""
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def run(script, *args):
    command = [sys.executable, str(ROOT / script), *args]
    subprocess.run(command, cwd=ROOT, check=True)


def main():
    parser = argparse.ArgumentParser(
        prog="image_studio.py",
        description="Detect, align, verify, and repair ImageStudio blue outlines.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("detect", help="Learn the 240 definitive blot centers")
    prepare = subparsers.add_parser("prepare", help="Pair visible blue centers to definitive targets")
    prepare.add_argument("--resume", action="store_true", help="Allow fewer visible outlines after a partial run")
    align = subparsers.add_parser("align", help="Drag current blue centers to their targets")
    align.add_argument("--targets", default="targets.json", help="Target JSON file to use")
    verify = subparsers.add_parser("verify", help="Check every visible blue center")
    verify.add_argument("--tolerance", type=float, default=10)
    complete = subparsers.add_parser("complete", help="Repair only verifier-reported misalignments")
    complete.add_argument("--tolerance", type=float, default=10)
    subparsers.add_parser("status", help="Run verification and return its status")

    args = parser.parse_args()
    if args.command == "detect":
        run("grid_detect.py")
    elif args.command == "prepare":
        run("prepare_targets.py", *( ["--resume"] if args.resume else [] ))
    elif args.command == "align":
        run("align.py", "--targets", args.targets)
    elif args.command in {"verify", "status"}:
        run("verify_alignment.py", "--tolerance", str(args.tolerance if args.command == "verify" else 10))
    elif args.command == "complete":
        run("complete_alignment.py", "--tolerance", str(args.tolerance))


if __name__ == "__main__":
    main()
