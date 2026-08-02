# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass
"""add_license_headers.py — Prepend license identifier comments to source files.

Walks the repository and prepends a license comment to every source file that
does not already contain one.  Markdown files and generated/cached output are
left untouched.

Supported file types and comment styles
----------------------------------------
  .py   .toml          #  SPDX-License-Identifier: Apache-2.0
  .cpp  .h             // SPDX-License-Identifier: Apache-2.0
  CMakeLists.txt       #  SPDX-License-Identifier: Apache-2.0

A file is considered to already have a license comment when it contains either
  "SPDX-License-Identifier"   or   "Apache License"
anywhere in the first 40 lines.

Run from the repo root:
    python add_license_headers.py [--dry-run]

Options:
    --dry-run   Print the files that would be modified without changing them.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Repository root — the folder that contains this script
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).parent.resolve()

# ---------------------------------------------------------------------------
# Directories whose contents are never touched
# ---------------------------------------------------------------------------
SKIP_DIRS: set[str] = {
    ".git",
    "build",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
}

# ---------------------------------------------------------------------------
# License header templates
# ---------------------------------------------------------------------------
_HASH_HEADER = """\
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass
"""

_SLASH_HEADER = """\
// SPDX-License-Identifier: Apache-2.0
// Copyright 2021 Christian Perwass
"""

# Map: file extension (lower-case, with dot) or exact filename → header string
_HEADERS: dict[str, str] = {
    ".py":   _HASH_HEADER,
    ".toml": _HASH_HEADER,
    ".h":    _SLASH_HEADER,
    ".cpp":  _SLASH_HEADER,
    "CMakeLists.txt": _HASH_HEADER,
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _header_for(path: Path) -> str | None:
    """Return the header string for *path*, or None if the file is not covered."""
    if path.name in _HEADERS:
        return _HEADERS[path.name]
    return _HEADERS.get(path.suffix.lower())


def _already_licensed(path: Path, check_lines: int = 40) -> bool:
    """Return True if the file already contains a license marker."""
    markers = ("SPDX-License-Identifier", "Apache License")
    try:
        with path.open(encoding="utf-8", errors="replace") as fh:
            for i, line in enumerate(fh):
                if i >= check_lines:
                    break
                if any(m in line for m in markers):
                    return True
    except OSError:
        return True  # skip unreadable files
    return False


def _collect_files(root: Path) -> list[Path]:
    """Yield all candidate files under *root*, skipping SKIP_DIRS."""
    results: list[Path] = []
    for path in root.rglob("*"):
        # Skip any path that contains a skipped directory name
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if not path.is_file():
            continue
        if _header_for(path) is not None:
            results.append(path)
    return sorted(results)


def _prepend(path: Path, header: str, dry_run: bool) -> None:
    """Prepend *header* to *path*.

    For Python files that start with a module docstring (``\"\"\"`` or
    ``'''``), the header is inserted *before* the docstring so the file
    remains importable and tools that read module docstrings still work.
    """
    original = path.read_text(encoding="utf-8")

    if dry_run:
        rel = path.relative_to(REPO_ROOT)
        print(f"  would add header → {rel}")
        return

    path.write_text(header + "\n" + original, encoding="utf-8")
    rel = path.relative_to(REPO_ROOT)
    print(f"  added header     → {rel}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Prepend SPDX license identifier to source files.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print which files would be modified without changing them.",
    )
    args = parser.parse_args(argv)

    candidates = _collect_files(REPO_ROOT)
    modified = 0
    skipped = 0

    for path in candidates:
        if _already_licensed(path):
            skipped += 1
            continue
        header = _header_for(path)
        assert header is not None  # guaranteed by _collect_files
        _prepend(path, header, dry_run=args.dry_run)
        modified += 1

    action = "would modify" if args.dry_run else "modified"
    print(
        f"\nDone: {action} {modified} file(s), "
        f"skipped {skipped} already-licensed file(s)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
