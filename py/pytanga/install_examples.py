# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Install packaged examples for local exploration."""

import shutil
from pathlib import Path


def _find_repo_root(start: Path) -> Path | None:
    """Walk up from *start* looking for a repository root indicator."""
    for candidate in [start, *start.parents]:
        if (candidate / ".git").exists() or (candidate / "pyproject.toml").exists():
            return candidate
    return None


def install_examples() -> Path:
    """Copy packaged (or dev) examples into the current project tree.

    Target directory: ``<repo-root>/.dep-examples/pytanga/`` (if a repo root is
    found by walking up from the current working directory) or
    ``./.dep-examples/pytanga/`` as fallback.

    When the function detects that it is running from an installed wheel (i.e.
    ``pytanga/_examples`` exists inside the package directory), the examples
    will be copied from there.  When running from a source checkout the
    examples will be copied directly from the repository's ``py/examples/``
    directory.
    """
    cwd = Path.cwd()
    repo = _find_repo_root(cwd)
    target_dir = (
        (repo / ".dep-examples" / "pytanga")
        if repo
        else (cwd / ".dep-examples" / "pytanga")
    )

    # ----- resolve the *source* of examples ------------------------------
    pkg_dir = Path(__file__).resolve().parent
    packaged = pkg_dir / "_examples"

    if packaged.is_dir():
        # installed wheel – copy the packaged examples
        source = packaged
    else:
        # dev / source checkout – copy the repo's py/examples/
        dev_repo = _find_repo_root(pkg_dir)
        if dev_repo is None:
            raise FileNotFoundError(
                "Cannot locate repository root for dev-mode examples. "
                "Make sure you are inside a tanga source checkout."
            )
        source = dev_repo / "py" / "examples"
        if not source.is_dir():
            raise FileNotFoundError(f"Expected examples directory not found: {source}")

    # ----- copy the examples --------------------------------------------
    target_dir.parent.mkdir(parents=True, exist_ok=True)
    if target_dir.is_symlink() or target_dir.is_file():
        target_dir.unlink()
    elif target_dir.is_dir():
        shutil.rmtree(target_dir)
    shutil.copytree(source, target_dir)

    return target_dir
