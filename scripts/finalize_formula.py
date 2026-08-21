#!/usr/bin/env python3
"""Fetch the released tarball and patch the Homebrew formula's url/sha256.

Usage: finalize_formula.py <version>

Called by the release workflow AFTER semantic-release has created the tag and
GitHub has generated the source tarball (v<version>.tar.gz). It downloads the
tarball, computes its real sha256, and rewrites Formula/siri-cli.rb so a
`brew install` points at the exact released source.

This replaces the prepare-time `git archive | gzip -n` guess, which did not
reliably match GitHub's generated tarball.
"""

import hashlib
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ORG = "Pasithea0"
REPO = "siri-cli"


def fetch_tarball_sha256(version: str) -> str:
    url = f"https://github.com/{ORG}/{REPO}/archive/refs/tags/v{version}.tar.gz"
    try:
        with urllib.request.urlopen(url, timeout=120) as resp:
            data = resp.read()
    except Exception as e:
        raise SystemExit(f"could not fetch {url}: {e}")
    return hashlib.sha256(data).hexdigest()


def update_formula(version: str, sha: str) -> None:
    path = ROOT / "Formula" / "siri-cli.rb"
    text = path.read_text()
    # Anchor to the TOP-LEVEL formula fields (2-space indent). The resource
    # blocks also contain url/sha256 but at 4-space indent — must not touch
    # those. (Resource urls point at pythonhosted.org, so the github.com url
    # regex is already unique, but the sha256 regex needs the 2-space anchor.)
    new_text, n = re.subn(
        r'(?m)^  url "https://github\.com/[^"]+?"',
        f'  url "https://github.com/{ORG}/{REPO}/archive/refs/tags/v{version}.tar.gz"',
        text,
    )
    if n != 1:
        raise SystemExit(f"Expected exactly 1 top-level url line in formula, found {n}")
    text = new_text
    new_text, n = re.subn(
        r'(?m)^  sha256 "[0-9a-f]{64}"',
        f'  sha256 "{sha}"',
        text,
    )
    if n != 1:
        raise SystemExit(f"Expected exactly 1 top-level sha256 line in formula, found {n}")
    path.write_text(new_text)
    print(f"formula updated: url v{version}, sha256 {sha[:12]}…")


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: finalize_formula.py <version>", file=sys.stderr)
        return 1
    version = sys.argv[1].lstrip("v")
    sha = fetch_tarball_sha256(version)
    update_formula(version, sha)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
