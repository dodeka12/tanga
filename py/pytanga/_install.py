# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Shared helpers for installing packaged docs/examples for AI-tool use."""

import shutil
import sys
from pathlib import Path


def find_repo_root(start: Path) -> Path | None:
    """Walk up from *start* looking for a repository root indicator."""
    for candidate in [start, *start.parents]:
        if (candidate / ".git").exists() or (candidate / "pyproject.toml").exists():
            return candidate
    return None


def replace_dir(source: Path, target_dir: Path, *, label: str) -> None:
    """Remove any existing *target_dir* and copy *source* into its place.

    The existing target is removed completely (file, symlink, or directory)
    before the copy, so the result is a faithful mirror of *source* rather than
    a merge over stale files.  Any failure to remove or copy prints an error
    message and raises :class:`OSError`, so callers never silently trust a
    partial install.
    """
    target_dir.parent.mkdir(parents=True, exist_ok=True)

    if target_dir.is_symlink() or target_dir.is_file():
        try:
            target_dir.unlink()
        except OSError as exc:
            print(
                f"ERROR: could not remove existing file {target_dir}: {exc}",
                file=sys.stderr,
            )
            raise
    elif target_dir.is_dir():
        try:
            shutil.rmtree(target_dir)
        except OSError as exc:
            print(
                f"ERROR: could not remove existing directory {target_dir}: {exc}",
                file=sys.stderr,
            )
            raise

    try:
        shutil.copytree(source, target_dir)
    except OSError as exc:
        # Don't leave a half-written mirror behind.
        if target_dir.exists():
            shutil.rmtree(target_dir, ignore_errors=True)
        print(
            f"ERROR: could not install {label} to {target_dir}: {exc}",
            file=sys.stderr,
        )
        raise
