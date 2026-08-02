# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Small utility helpers for the Tanga 3D viewer package."""

from __future__ import annotations


def _is_jupyter() -> bool:
    """Detect whether we are running inside a Jupyter notebook/IPython."""
    try:
        from IPython import get_ipython  # type: ignore[import-untyped]

        shell = get_ipython()
        return shell is not None and hasattr(shell, "kernel")
    except ImportError:
        return False
