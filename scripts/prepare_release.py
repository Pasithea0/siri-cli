#!/usr/bin/env python3
"""Bump the project version in pyproject.toml (called by semantic-release).

Usage: prepare_release.py <new_version>

semantic-release invokes this via @semantic-release/exec prepareCmd with the
next release version as ${nextRelease.version}. It only bumps pyproject.toml
here; the Homebrew formula's url/sha256 are updated AFTER the tag is created,
by scripts/finalize_formula.py (run in the release workflow), because the
tarball sha256 can only be known once GitHub has generated the source tarball.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def bump_pyproject(new_version: str) -> None:
    path = ROOT / "pyproject.toml"
    text = path.read_text()
    new_text, n = re.subn(
        r'(?m)^(version\s*=\s*)"[^"]+"',
        rf'\1"{new_version}"',
        text,
    )
    if n != 1:
        raise RuntimeError(f"Expected exactly 1 version key in {path}, found {n}")
    path.write_text(new_text)
    print(f"pyproject.toml version -> {new_version}")


def bump_version_init(new_version: str) -> None:
    """Bump __version__ in src/siri_cli/__init__.py so `siri --version`
    reports the released version instead of a stale hardcoded value."""
    path = ROOT / "src" / "siri_cli" / "__init__.py"
    text = path.read_text()
    new_text, n = re.subn(
        r'(?m)^(__version__\s*=\s*)"[^"]+"',
        rf'\1"{new_version}"',
        text,
    )
    if n != 1:
        raise RuntimeError(f"Expected exactly 1 __version__ in {path}, found {n}")
    path.write_text(new_text)
    print(f"__init__.py __version__ -> {new_version}")


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: prepare_release.py <new_version>", file=sys.stderr)
        return 1
    new_version = sys.argv[1].lstrip("v")
    bump_pyproject(new_version)
    bump_version_init(new_version)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
