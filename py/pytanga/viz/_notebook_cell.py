# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Resolve the id of the notebook cell currently being executed.

Notebooks carry a persistent per-cell id (JEP 62). The IPython kernel exposes
it to ``InteractiveShell.run_cell`` as ``cell_id`` and fires a ``pre_run_cell``
event whose ``info`` object carries ``cell_id``.  We register a listener at
import time so :mod:`pytanga.viz` can use the cell id as a stable per-cell
viewer key without requiring a separate setup cell.
"""

from __future__ import annotations

_cell_id: str | None = None


def _on_pre_run_cell(info: object) -> None:
    global _cell_id
    _cell_id = getattr(info, "cell_id", None) or None


def _register() -> None:
    try:
        from IPython import get_ipython
    except ImportError:
        return
    shell = get_ipython()
    if shell is None or not hasattr(shell, "events"):
        return
    try:
        shell.events.register("pre_run_cell", _on_pre_run_cell)
    except Exception:
        pass


_register()


def current_cell_id() -> str | None:
    """Return the id of the notebook cell currently executing, or ``None``."""
    return _cell_id
