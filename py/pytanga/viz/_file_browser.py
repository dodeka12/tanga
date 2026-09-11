# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Server-side filesystem listing for the frontend file browser.

The frontend never reads the filesystem directly; it asks the backend (which
runs on the same machine whose files are browsed) via ``file_browser_navigate``
and renders the ``file_browser_listing`` reply produced by
:func:`list_directory`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def list_directory(
    path: str,
    *,
    root: str | None = None,
    show_hidden: bool = False,
) -> dict[str, Any]:
    """List the directory at *path* for the file browser.

    Returns ``{"path": <str>, "parent": <str|None>, "entries": [...],
    "error": <str|None>}`` where each entry is ``{"name", "path", "is_dir"}`` —
    directories first, then alphabetical, dot-files omitted unless *show_hidden*.

    When *root* is given, the resolved directory is clamped to it (the browser
    cannot navigate above the root).  Otherwise the home directory is used as
    the starting point for relative paths but is not a hard boundary.
    """
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
                entries.append(
                    {
                        "name": child.name,
                        "path": str(child),
                        "is_dir": child.is_dir(),
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
