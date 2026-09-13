# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Internal helper functions for the entity data classes.

The MV-conversion registry now lives in :mod:`pytanga.entity._util`; this
module re-exports it for backward compatibility and keeps the geometry-specific
``_compute_start_direction`` helper.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pytanga.entity._util import (
    _convert_mv,
    _fmt_v,
    _is_mv,
    _scalar,
    register_analyzer,
)

if TYPE_CHECKING:
    from .direction import Direction

__all__ = [
    "_compute_start_direction",
    "_convert_mv",
    "_fmt_v",
    "_is_mv",
    "_scalar",
    "register_analyzer",
]


def _compute_start_direction(axis: "Direction") -> "Direction":
    """Return a deterministic unit vector perpendicular to *axis*.

    Picks the coordinate axis least aligned with *axis* so the cross product is
    well-conditioned, then returns ``axis × ref`` normalized.  This guarantees
    the frontend always receives a valid in-plane start direction.
    """
    from .direction import Direction

    a = axis.normalized()
    refs = (
        Direction(1.0, 0.0, 0.0),
        Direction(0.0, 1.0, 0.0),
        Direction(0.0, 0.0, 1.0),
    )
    ref = min(refs, key=lambda r: abs(a.dot(r)))
    start = a.cross(ref)
    if start.mag() == 0.0:  # defensive: never expected to trigger
        for r in refs:
            candidate = a.cross(r)
            if candidate.mag() != 0.0:
                return candidate.normalized()
    return start.normalized()
