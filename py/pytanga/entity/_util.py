# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""MV-conversion registry and helpers for the fundamental entity classes.

The registry decouples the fundamental entities (``Point``/``Direction``/…)
from the algebra-specific analyzers: :mod:`pytanga.geometry.analysis`
registers ``analyze_<name>(mv)`` callables at import time, so an entity
constructor can route an MV through the full analyzer without importing
``analysis`` (which in turn imports the entities).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pytanga.algebra._mv import MV
    from typing_extensions import TypeIs


def _fmt_v(x: float, y: float, z: float) -> str:
    """Format a 3D vector with 2 decimal places."""
    return f"({x:.2f}, {y:.2f}, {z:.2f})"


def _is_mv(x: object) -> "TypeIs[MV]":
    """True if *x* is a multivector (has the ``_alg`` slot)."""
    return hasattr(x, "_alg")


# Registry of ``analyze_<name>(mv)`` functions, populated by
# ``pytanga.geometry.analysis`` once all dispatchers are defined.  This keeps
# the entity constructors free of any import-time dependency on ``analysis``.
_ANALYZERS: dict[str, "Callable[[MV], Any]"] = {}


def register_analyzer(name: str, fn: "Callable[[MV], Any]") -> None:
    """Register an algebra-specific analyzer callable under *name*.

    Called by :mod:`pytanga.geometry.analysis` during import.  *fn* must
    accept a single MV and return the matching entity dataclass.
    """
    _ANALYZERS[name] = fn


def _convert_mv(name: str, mv: "MV") -> Any:
    """Convert an MV to an entity via the registered analyzer for *name*."""
    try:
        analyzer = _ANALYZERS[name]
    except KeyError:
        raise RuntimeError(
            f"No analyzer registered for {name!r}; import pytanga.geometry first."
        ) from None
    return analyzer(mv)


def _scalar(value: "MV" | float) -> float:
    """Return the python scalar for a scalar MV, or *value* unchanged."""
    if _is_mv(value):
        if not value.is_scalar:
            raise ValueError("Expected a scalar multivector")
        return value.scalar
    return value
