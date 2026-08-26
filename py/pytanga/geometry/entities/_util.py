# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Internal helper functions for the entity data classes.

These helpers keep the individual entity modules free of duplicated
utilities and of import-time cycles between ``point``/``direction`` and
the composite entities.
"""

from __future__ import annotations


def _fmt_v(x: float, y: float, z: float) -> str:
    """Format a 3D vector with 2 decimal places."""
    return f"({x:.2f}, {y:.2f}, {z:.2f})"


def _is_mv(x) -> bool:
    """True if *x* is a multivector (has the ``_alg`` slot)."""
    return hasattr(x, "_alg")


# Registry of ``analyze_<name>(mv)`` functions, populated by
# ``pytanga.geometry.analysis`` once all dispatchers are defined.  This keeps
# ``entities`` free of any import-time dependency on ``analysis`` (which in
# turn imports ``entities``), while still letting entity constructors route
# an MV through the full, algebra-specific analyzer.
_ANALYZERS: dict[str, "callable"] = {}


def register_analyzer(name: str, fn) -> None:
    """Register an algebra-specific analyzer callable under *name*.

    Called by :mod:`pytanga.geometry.analysis` during import.  *fn* must
    accept a single MV and return the matching entity dataclass.
    """
    _ANALYZERS[name] = fn


def _convert_mv(name: str, mv):
    """Convert an MV to an entity via the registered analyzer for *name*."""
    try:
        analyzer = _ANALYZERS[name]
    except KeyError:
        raise RuntimeError(
            f"No analyzer registered for {name!r}; import pytanga.geometry first."
        ) from None
    return analyzer(mv)


def _scalar(value):
    """Return the python scalar for a scalar MV, or *value* unchanged."""
    if _is_mv(value):
        if not value.is_scalar:
            raise ValueError("Expected a scalar multivector")
        return value.scalar
    return value

def _compute_start_direction(axis) -> "Direction":
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

