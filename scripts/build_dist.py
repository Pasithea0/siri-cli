#!/usr/bin/env python3
"""Build sdist + wheel artifacts (called by semantic-release publishCmd).

The built files in dist/ are attached to the GitHub release by
@semantic-release/github.
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "--quiet", "build"],
        check=True,
    )
    subprocess.run(
        [sys.executable, "-m", "build", "--outdir", str(ROOT / "dist")],
        check=True,
    )
    print("built dist/ artifacts")
    for p in sorted((ROOT / "dist").glob("*")):
        print(" ", p.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
