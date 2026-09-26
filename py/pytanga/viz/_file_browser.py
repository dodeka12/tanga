# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Server-side filesystem listing for the frontend file browser.

The frontend never reads the filesystem directly; it asks the backend (which
runs on the same machine whose files are browsed) via ``file_browser_navigate``
and renders the ``file_browser_listing`` reply produced by
:func:`list_directory`.
"""

from __future__ import annotations

import fnmatch
from pathlib import Path
from typing import Any


def list_directory(
    path: str,
    *,
    root: str | None = None,
    show_hidden: bool = False,
    file_filter: str = "",
    folders_only: bool = False,
) -> dict[str, Any]:
    """List the directory at *path* for the file browser.

    Returns ``{"path": <str>, "parent": <str|None>, "entries": [...],
    "error": <str|None>}`` where each entry is ``{"name", "path", "is_dir"}`` —
    directories first, then alphabetical, dot-files omitted unless *show_hidden*.

    *file_filter* filters non-directory entries to a comma/space-separated,
    case-insensitive list of extensions (``.png``/``png``) and/or full-filename
    glob patterns (``hello_*.png``, ``*.exr``); empty = all files.
    *folders_only* drops files entirely, leaving only directories.

    When *root* is given, the resolved directory is clamped to it (the browser
    cannot navigate above the root).  Otherwise the home directory is used as
    the starting point for relative paths but is not a hard boundary.
    """
    tokens = _parse_file_filter(file_filter)
    try:
        root_path = Path(root).expanduser().resolve() if root else None
    except OSError:
        root_path = None

    raw = str(path or "")
    try:
        p = Path(raw).expanduser()
        if not p.is_absolute():
            base = root_path if root_path is not None else Path.home()
            p = base / p
        p = p.resolve()

        if root_path is not None and not p.is_relative_to(root_path):
            p = root_path

        if not p.is_dir():
            return {
                "path": str(p),
                "parent": str(p.parent),
                "entries": [],
                "error": "missing",
            }

        entries: list[dict[str, Any]] = []
        try:
            for child in p.iterdir():
                if not show_hidden and child.name.startswith("."):
                    continue
                is_dir = child.is_dir()
                if folders_only and not is_dir:
                    continue
                if not is_dir and tokens and not _matches_file(child.name, tokens):
                    continue
                entries.append(
                    {
                        "name": child.name,
                        "path": str(child),
                        "is_dir": is_dir,
                    }
                )
        except PermissionError:
            return {
                "path": str(p),
                "parent": str(p.parent),
                "entries": [],
                "error": "permission",
            }

        entries.sort(key=lambda e: (not e["is_dir"], e["name"].lower()))
        return {
            "path": str(p),
            "parent": str(p.parent),
            "entries": entries,
            "error": None,
        }
    except PermissionError:
        return {"path": raw, "parent": None, "entries": [], "error": "permission"}
    except OSError:
        return {"path": raw, "parent": None, "entries": [], "error": "missing"}


def _parse_file_filter(file_filter: str) -> list[str]:
    """Split a *file_filter* string into case-insensitive match tokens."""
    tokens = file_filter.replace(",", " ").replace(";", " ").split()
    return [token for token in tokens if token]


def _matches_file(name: str, tokens: list[str]) -> bool:
    """Return True when *name* matches any extension or glob token in *tokens*."""
    lower = name.lower()
    for token in tokens:
        pattern = token.lower()
        if any(ch in pattern for ch in "*?["):
            if fnmatch.fnmatchcase(lower, pattern):
                return True
        else:
            ext = pattern.lstrip(".")
            if ext and lower.endswith("." + ext):
                return True
    return False
