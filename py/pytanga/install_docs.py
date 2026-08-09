# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Install packaged documentation for AI-tool consumption."""

import os
import shutil
from pathlib import Path


def _find_repo_root(start: Path) -> Path | None:
    """Walk up from *start* looking for a repository root indicator."""
    for candidate in [start, *start.parents]:
        if (candidate / ".git").exists() or (candidate / "pyproject.toml").exists():
            return candidate
    return None


def install_docs() -> Path:
    """Copy packaged (or dev) docs into the current project tree.

    Target directory: ``<repo-root>/.dep-docs/pytanga/`` (if a repo root is
    found by walking up from the current working directory) or
    ``./.dep-docs/pytanga/`` as fallback.

    When the function detects that it is running from an installed wheel (i.e.
    ``pytanga/_docs`` exists inside the package directory), the docs will be
    copied from there.  When running from a source checkout the docs will be
    copied directly from the repository's top-level ``docs/`` directory.
    """
    cwd = Path.cwd()
    repo = _find_repo_root(cwd)
    target_dir = (
        (repo / ".dep-docs" / "pytanga") if repo else (cwd / ".dep-docs" / "pytanga")
    )

    # ----- resolve the *source* of docs ---------------------------------
    pkg_dir = Path(__file__).resolve().parent
    packaged = pkg_dir / "_docs"

    if packaged.is_dir():
        # installed wheel – copy the packaged docs
        source = packaged
    else:
        # dev / source checkout – copy the repo's top-level docs/
        dev_repo = _find_repo_root(pkg_dir)
        if dev_repo is None:
            raise FileNotFoundError(
                "Cannot locate repository root for dev-mode docs. "
                "Make sure you are inside a tanga source checkout."
            )
        source = dev_repo / "docs"
        if not source.is_dir():
            raise FileNotFoundError(f"Expected docs directory not found: {source}")

    # ----- copy the docs -------------------------------------------------
    target_dir.parent.mkdir(parents=True, exist_ok=True)
    if target_dir.is_symlink() or target_dir.is_file():
        target_dir.unlink()
    elif target_dir.is_dir():
        shutil.rmtree(target_dir)
    shutil.copytree(source, target_dir)

    return target_dir
