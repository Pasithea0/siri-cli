#!/usr/bin/env python3
"""Bump version + update the Homebrew formula (called by semantic-release).

Usage: prepare_release.py <new_version>

semantic-release invokes this via @semantic-release/exec prepareCmd with the
next release version as ${nextRelease.version}. It runs BEFORE the
@semantic-release/git plugin commits, so both the pyproject version bump and
the formula url/sha256 rewrite land in the same release commit.

The tarball sha256 is computed locally with `git archive | gzip -n`, which is
the deterministic method GitHub uses to generate its source tarballs, so the
committed sha256 matches the auto-generated tarball for the future tag.
"""

import hashlib
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ORG = "Pasithea0"
REPO = "siri-cli"


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


def tarball_sha256() -> str:
    """Compute the deterministic GitHub source-tarball sha256 via git archive."""
    # GitHub generates source tarballs reproducibly as: git archive | gzip -n
    # (since ~2023). Reproduce exactly so the sha256 matches the released tarball.
    archive = subprocess.run(
        ["git", "-C", str(ROOT), "archive", "--format=tar", "HEAD"],
        capture_output=True,
    )
    if archive.returncode != 0:
        raise RuntimeError("git archive failed")
    gz = subprocess.run(
        ["gzip", "-n"],
        input=archive.stdout,
        capture_output=True,
    )
    if gz.returncode != 0:
        raise RuntimeError("gzip failed")
    return hashlib.sha256(gz.stdout).hexdigest()


def update_formula(version: str, sha: str) -> None:
    path = ROOT / "Formula" / "siri-cli.rb"
    text = path.read_text()
    new_text, n = re.subn(
        r'url "https://github\.com/[^"]+?"',
        f'url "https://github.com/{ORG}/{REPO}/archive/refs/tags/v{version}.tar.gz"',
        text,
    )
    if n != 1:
        raise RuntimeError(f"Expected exactly 1 url line in formula, found {n}")
    text = new_text
    new_text, n = re.subn(
        r'sha256 "[0-9a-f]{64}"',
        f'sha256 "{sha}"',
        text,
    )
    if n != 1:
        raise RuntimeError(f"Expected exactly 1 sha256 line in formula, found {n}")
    path.write_text(new_text)
    print(f"formula updated: url v{version}, sha256 {sha[:12]}…")


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: prepare_release.py <new_version>", file=sys.stderr)
        return 1
    new_version = sys.argv[1].lstrip("v")
    bump_pyproject(new_version)
    sha = tarball_sha256()
    update_formula(new_version, sha)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
