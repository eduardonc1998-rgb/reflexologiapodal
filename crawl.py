#!/usr/bin/env python3
"""Capture the one-page sales funnel locally with Playwright (no checkout submission)."""
from pathlib import Path
import argparse
import os
import subprocess
import sys

HERE = Path(__file__).resolve().parent

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--url", default="http://127.0.0.1:8000/")
    ap.add_argument("--out", type=Path, default=HERE / "capture_landing")
    ap.add_argument("--node", default="node", help="Node.js executable")
    ap.add_argument("--node-modules", help="folder containing playwright")
    ap.add_argument("--browser", help="installed Chrome/Edge executable if Playwright's bundled browser is unavailable")
    a = ap.parse_args()
    env = os.environ.copy()
    if a.node_modules:
        env["NODE_PATH"] = str(Path(a.node_modules).resolve())
    cmd = [a.node, str(HERE / "crawl_browser.cjs"), a.url, str(a.out.resolve()), a.browser or ""]
    try:
        return subprocess.run(cmd, env=env, check=False).returncode
    except FileNotFoundError:
        print("Node.js was not found. Install Node.js and Playwright, then pass --node and --node-modules.", file=sys.stderr)
        return 2

if __name__ == "__main__": raise SystemExit(main())
