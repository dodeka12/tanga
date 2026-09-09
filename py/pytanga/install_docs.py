# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Install packaged documentation for AI-tool consumption."""

from pathlib import Path

from ._install import find_repo_root, replace_dir


def install_docs() -> Path:
    """Copy packaged (or dev) docs into the current project tree.

    Target directory: ``<repo-root>/.dep-docs/pytanga/`` (if a repo root is
    found by walking up from the current working directory) or
    ``./.dep-docs/pytanga/`` as fallback.

    When the function detects that it is running from an installed wheel (i.e.
    ``pytanga/_docs`` exists inside the package directory), the docs will be
    copied from there.  When running from a source checkout the docs will be
    copied directly from the repository's top-level ``docs/`` directory.

    Any previously installed docs are removed first, so the target is always a
    faithful mirror of the packaged docs.  Raises :class:`OSError` (after
    printing an error message) if the old copy cannot be removed or the new one
    cannot be written.
    """
    cwd = Path.cwd()
    repo = find_repo_root(cwd)
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
        dev_repo = find_repo_root(pkg_dir)
        if dev_repo is None:
            raise FileNotFoundError(
                "Cannot locate repository root for dev-mode docs. "
                "Make sure you are inside a tanga source checkout."
            )
        source = dev_repo / "docs"
        if not source.is_dir():
            raise FileNotFoundError(f"Expected docs directory not found: {source}")

    replace_dir(source, target_dir, label="docs")

    return target_dir
