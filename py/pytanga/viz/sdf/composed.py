# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Composed SDF drawable object (a fixed combine tree).

A :class:`Composed` folds several members into one SDF object using each
member's ``combine`` mode. Members are :class:`~pytanga.viz.sdf.SdfElement`s
(``SdfObject``/``Combine``/nested ``Composed``/``SdfGroup``) or low-level
``SdfNode`` primitives, coerced at construction.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any

from ._compose import ECompose, SdfElement, _normalize_part
from .primitives import SdfNode, group


@dataclass(init=False)
class Composed(SdfElement):
    """A fixed SDF combine tree: members folded by their ``combine`` modes.

    Each part is a bare element (defaults to union), a unary-tagged element
    (``-el`` / ``~el``), or a legacy ``(obj, mode)`` tuple/string. ``obj`` may be
    a geometry entity, an ``SdfNode``, an ``SdfObject``/``Combine``, or a nested
    ``Composed``/``SdfGroup``.

    Example::

        Composed(sphere(1.0), (capped_cylinder(0.6, 0.4), "subtract"), id="bead")
    """

    parts: tuple[tuple[Any, ECompose], ...]
    id: str | None

    def __init__(
        self,
        *parts: Any,
        id: str | None = None,
        combine: ECompose = ECompose.UNION,
        smoothness: float | None = None,
    ) -> None:
        object.__setattr__(self, "parts", tuple(_normalize_part(p) for p in parts))
        object.__setattr__(self, "id", id)
        object.__setattr__(self, "combine", combine)
        object.__setattr__(self, "smoothness", smoothness)

    def to_sdf_node(self) -> SdfNode:
        children: list[SdfNode] = []
        for element, mode in self.parts:
            child = copy.copy(_member_node(element))
            child.combine = mode.value
            child.smoothness = getattr(element, "smoothness", None)
            children.append(child)
        return group(children, id=self.id)


def _member_node(element: Any) -> SdfNode:
    """Lower a member (``SdfNode`` or ``SdfElement``) to an ``SdfNode``."""
    if isinstance(element, SdfNode):
        return element
    return element.to_sdf_node()
