# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Size value type for the Tanga 3D viewer's split-view layout.

A ``Size`` is a numeric extent along one axis together with a unit that
determines how it is interpreted relative to the available space:

- ``px``   — absolute CSS pixels.
- ``%``    — a fraction of the parent extent along the same axis.
- ``fr``   — a flexible share (only meaningful as a *preferred* size inside a
  container; it has no absolute extent on its own).
- ``auto`` — unconstrained (min → 0, max → ∞, preferred → natural size).

This is the Python mirror of the frontend ``Size`` value object
(``templates/views/size.js``); both parse/emit the same JSON shape
``{"value": <float>, "unit": "<unit>"}``.  ``None`` ("no constraint") is
treated as ``auto`` when resolving min/max bounds.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Unit = Literal["px", "%", "fr", "auto"]

_UNITS = ("px", "%", "fr", "auto")


@dataclass(frozen=True)
class Size:
    """An extent along one axis with a resolution unit."""

    value: float
    unit: Unit = "px"

    def __post_init__(self) -> None:
        if self.unit not in _UNITS:
            raise ValueError(
                f"Unknown size unit {self.unit!r}; expected one of {_UNITS}"
            )

    # -- factories -------------------------------------------------

    @classmethod
    def px(cls, value: float) -> "Size":
        """A fixed pixel extent."""
        return cls(float(value), "px")

    @classmethod
    def percent(cls, value: float) -> "Size":
        """A percentage of the parent extent along the same axis."""
        return cls(float(value), "%")

    @classmethod
    def fr(cls, value: float) -> "Size":
        """A flexible share (preferred sizes only)."""
        return cls(float(value), "fr")

    @classmethod
    def auto(cls) -> "Size":
        """An unconstrained extent."""
        return cls(0.0, "auto")

    # -- (de)serialization ----------------------------------------

    @classmethod
    def from_dict(cls, data: dict) -> "Size":
        """Build a ``Size`` from the canonical ``{"value", "unit"}`` JSON shape."""
        if not isinstance(data, dict):
            raise TypeError(f"Expected a dict, got {type(data).__name__}")
        try:
            value = float(data["value"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(
                f"Size dict must have a numeric 'value': {data!r}"
            ) from exc
        unit = data.get("unit", "px")
        return cls(value, unit)

    def to_dict(self) -> dict:
        """Serialize to the canonical ``{"value", "unit"}`` JSON shape."""
        return {"value": self.value, "unit": self.unit}

    # -- resolution -----------------------------------------------

    def resolve(self, available: float, natural: float | None = None) -> float | None:
        """Resolve this size to pixels given *available* parent extent.

        ``px`` returns its value; ``%`` scales by *available*.  ``fr`` and
        ``auto`` have no absolute extent, so they defer to *natural* (which is
        ``0`` for a minimum, ``None``/unbounded for a maximum, and the view's
        natural size for a preferred extent).
        """
        if self.unit == "px":
            return self.value
        if self.unit == "%":
            return self.value / 100.0 * float(available)
        return natural

    # -- helpers --------------------------------------------------

    def clone(self) -> "Size":
        """Return an equal but distinct copy."""
        return Size(self.value, self.unit)


#: A size or no constraint (``None`` ⇄ unconstrained).
SizeSpec = Size | None


def size_from_dict(data: dict | None) -> SizeSpec:
    """Parse ``None`` → ``None`` and a dict → :class:`Size`."""
    if data is None:
        return None
    return Size.from_dict(data)
