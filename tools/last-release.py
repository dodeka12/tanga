#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Print the latest stable release tag the current branch is based on.

Walks back from the merge-base of the current branch with ``main`` and prints
the most recent non-prerelease (no ``-rcN`` suffix) version tag, without the
leading ``v``. This is the version to use in changelog titles
(``# Changes since version <this>``).

Usage:
  uv run python tools/last-release.py            # current branch vs main
  uv run python tools/last-release.py <ref>      # explicit ref (commit/tag/branch)
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys

RC_RE = re.compile(r"-rc\d+$")


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], capture_output=True, text=True, check=True
    ).stdout.strip()


def version_key(tag: str) -> tuple[int, ...]:
    ver = tag[1:] if tag.startswith("v") else tag
    ver = ver.split("-", 1)[0]  # drop any prerelease suffix
    return tuple(int(p) for p in ver.split(".") if p.isdigit())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Print the latest stable release tag the current branch is based on."
    )
    parser.add_argument("ref", nargs="?", default="HEAD")
    parser.add_argument("--main", default="main", help="base branch (default: main)")
    args = parser.parse_args(argv)

    base = git("merge-base", args.main, args.ref)
    tags = git("tag", "--merged", base).splitlines()
    stable = [t for t in tags if not RC_RE.search(t)]
    if not stable:
        print("No stable (non-prerelease) release tag found.", file=sys.stderr)
        return 1

    latest = max(stable, key=version_key)
    print(latest[1:] if latest.startswith("v") else latest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
