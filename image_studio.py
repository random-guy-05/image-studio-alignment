#!/usr/bin/env python3
"""Friendly command-line entry point for the ImageStudio workflow."""
import argparse
import subprocess
import sys
from pathlib import Path
from escape_guard import AbortRequested, check, sleep as safe_sleep, start as start_escape, stop as stop_escape

ROOT = Path(__file__).resolve().parent
WORKDIR = Path.cwd()


def run(script, *args):
    command = [sys.executable, str(ROOT / script), *args]
    process = subprocess.Popen(command, cwd=WORKDIR)
    try:
        while process.poll() is None:
            check()
            safe_sleep(0.05)
    except AbortRequested:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
        raise
    if process.returncode:
        raise subprocess.CalledProcessError(process.returncode, command)


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
    verify.add_argument("--tolerance", type=float, default=10)
    complete = subparsers.add_parser("complete", help="Repair only verifier-reported misalignments")
    complete.add_argument("--tolerance", type=float, default=10)
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
    start_escape()
    try:
        if args.command == "run":
            run("grid_detect.py")
            run("prepare_targets.py")
            run("align.py")
            run("verify_alignment.py")
        elif args.command == "detect":
            run("grid_detect.py")
        elif args.command == "prepare":
            run("prepare_targets.py", *( ["--resume"] if args.resume else [] ))
        elif args.command == "align":
            run("align.py", "--targets", args.targets)
        elif args.command in {"verify", "status"}:
            run("verify_alignment.py", "--tolerance", str(args.tolerance if args.command == "verify" else 10))
        elif args.command == "complete":
            run("complete_alignment.py", "--tolerance", str(args.tolerance))
    except AbortRequested:
        print("\nAborted by ESC.", file=sys.stderr)
        raise SystemExit(130)
    finally:
        stop_escape()


if __name__ == "__main__":
    main()
