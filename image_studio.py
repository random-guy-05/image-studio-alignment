#!/usr/bin/env python3
"""Friendly command-line entry point for the ImageStudio workflow."""
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WORKDIR = Path.cwd()


def run(script, *args):
    command = [sys.executable, str(ROOT / script), *args]
    subprocess.run(command, cwd=WORKDIR, check=True)


def main():
    parser = argparse.ArgumentParser(
        prog="image_studio.py",
        description="Detect, align, verify, and repair ImageStudio blue outlines.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("detect", help="Learn the 240 definitive blot centers")
    subparsers.add_parser("init", help="Create a local screenshots workspace")
    subparsers.add_parser("clean", help="Remove generated workspace files")
    subparsers.add_parser("run", help="Run detect, prepare, align, and verify")
    prepare = subparsers.add_parser("prepare", help="Pair visible blue centers to definitive targets")
    prepare.add_argument("--resume", action="store_true", help="Allow fewer visible outlines after a partial run")
    align = subparsers.add_parser("align", help="Drag current blue centers to their targets")
    align.add_argument("--targets", default="targets.json", help="Target JSON file to use")
    verify = subparsers.add_parser("verify", help="Check every visible blue center")
    verify.add_argument("--tolerance", type=float, default=5)
    complete = subparsers.add_parser("complete", help="Repair only verifier-reported misalignments")
    complete.add_argument("--tolerance", type=float, default=5)
    subparsers.add_parser("status", help="Run verification and return its status")

    args = parser.parse_args()
    if args.command == "init":
        (WORKDIR / "screenshots").mkdir(parents=True, exist_ok=True)
        print(f"Workspace ready: {WORKDIR}")
        print(f"Put the clean full-screen blot screenshot at: {WORKDIR / 'screenshots' / 'dots.png'}")
        return
    if args.command == "clean":
        for f in ["predicted_positions.json", "targets.json", "verification.json",
                  "resume_targets.json", "screenshots/detected_overlay.png"]:
            p = WORKDIR / f
            if p.exists():
                p.unlink()
                print(f"  removed {f}")
        print("Workspace cleaned. Screenshots/dots.png preserved.")
        return
    if not (WORKDIR / "screenshots" / "dots.png").exists():
        parser.error(f"No screenshots/dots.png in {WORKDIR}. Run `image-studio init` first.")
    if args.command == "run":
        run("grid_detect.py")
        print()
        try:
            resp = input("Proceed with alignment? (y/n) [y]: ").strip().lower()
            if resp and resp != "y":
                print("Aborted. Overlay saved — review screenshots/detected_overlay.png")
                return
        except (EOFError, KeyboardInterrupt):
            print("\nAborted.")
            return
        run("prepare_targets.py")
        run("align.py")
        try:
            run("verify_alignment.py")
        except subprocess.CalledProcessError:
            pass  # non-zero = misalignments found; that's a report, not a crash
    elif args.command == "detect":
        run("grid_detect.py")
    elif args.command == "prepare":
        run("prepare_targets.py", *( ["--resume"] if args.resume else [] ))
    elif args.command == "align":
        run("align.py", "--targets", args.targets)
    elif args.command in {"verify", "status"}:
        try:
            run("verify_alignment.py", "--tolerance", str(args.tolerance if args.command == "verify" else 5))
        except subprocess.CalledProcessError:
            pass
    elif args.command == "complete":
        try:
            run("complete_alignment.py", "--tolerance", str(args.tolerance))
        except subprocess.CalledProcessError:
            pass


if __name__ == "__main__":
    main()
