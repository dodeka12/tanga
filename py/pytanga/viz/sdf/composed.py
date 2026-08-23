# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Composed SDF drawable object.

A :class:`Composed` bundles several constituents into a single drawable SDF
object: one scene entry, one material (color/opacity), and a per-constituent
combine mode (``union`` / ``intersection`` / ``subtract``). It serializes to a
``group`` combinator node whose children each carry their own ``combine``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

_COMBINE_MODES = ("union", "intersection", "subtract")


@dataclass(frozen=True)
class Composed:
    """A drawable SDF object built from constituents, each with its own combine mode.

    Each part is either a bare object (defaults to ``"union"``) or an
    ``(object, combine_mode)`` pair. ``object`` may be a geometry entity, an
    operator, a :class:`~pytanga.viz.sdf.primitives.SdfNode`, or another
    ``Composed`` (nesting).

    Example::

        Composed(sphere(1.0), (capped_cylinder(0.6, 0.4), "subtract"))
    """

    parts: tuple[tuple[Any, str], ...]

    def __init__(self, *parts: Any) -> None:
        normalized: list[tuple[Any, str]] = []
        for part in parts:
            if (
                isinstance(part, tuple)
                and len(part) == 2
                and isinstance(part[1], str)
            ):
                obj, combine_mode = part
            else:
                obj, combine_mode = part, "union"
            if combine_mode not in _COMBINE_MODES:
                raise ValueError(
                    f"Invalid combine mode {combine_mode!r}; expected one of "
                    f"{_COMBINE_MODES}"
                )
            normalized.append((obj, combine_mode))
        object.__setattr__(self, "parts", tuple(normalized))
