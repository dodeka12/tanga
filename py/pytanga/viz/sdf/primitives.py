# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""SDF primitive/combinator descriptor model for the analytic entity path.

These dataclasses describe an SDF tree in a JSON-friendly, frontend-consumable
form. The frontend ``scene-builder.js`` dispatches on ``kind`` to emit the
matching GLSL expression (mirroring the existing ``renderers/factory.js``
layout). Primitives take their point in *local* space; a ``transform`` places
them in world space (or clips an infinite entity via an explicit ``bound``).

The ``kind`` strings are the shared vocabulary between Python and the GLSL
library in ``templates/sdf/shaders/primitives.glsl``:

    sphere, box, cylinder, cappedCylinder, torus  (+ ``bound`` = a clip box)

Combinators fold child trees with IQ sign-preserving min/max:

    union, intersect, subtract
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SdfNode:
    """One SDF tree node (a primitive or a combinator).

    Attributes:
        kind: The node kind (primitive or combinator name).
        params: Typed parameters for the primitive (radius, halfExtents, …).
        transform: Optional ``{"position": [x,y,z], "rotation": {"axis":
            [x,y,z], "angle": float}}`` world transform.
        children: Child nodes for combinators (``None`` for primitives).
    """

    kind: str
    params: dict[str, Any] = field(default_factory=dict)
    transform: dict[str, Any] | None = None
    children: list["SdfNode"] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-ready dict, omitting empty sections."""
        result: dict[str, Any] = {"kind": self.kind}
        if self.params:
            result["params"] = self.params
        if self.transform:
            result["transform"] = self.transform
        if self.children:
            result["children"] = [c.to_dict() for c in self.children]
        return result


def primitive(
    kind: str,
    params: dict[str, Any] | None = None,
    *,
    position: tuple[float, float, float] | None = None,
    rotation: tuple[tuple[float, float, float], float] | None = None,
    **extra_params: Any,
) -> SdfNode:
    """Build a primitive node with an optional world transform.

    Args:
        kind: The primitive kind (see module docstring).
        params: Typed primitive parameters.
        position: World-space translation to apply to the primitive.
        rotation: ``(axis, angle_radians)`` world-space rotation (align the
            primitive's canonical axis onto the target direction).
        **extra_params: Additional typed parameters folded into ``params``.
    """
    merged: dict[str, Any] = dict(params or {})
    merged.update(extra_params)
    transform = _make_transform(position=position, rotation=rotation)
    return SdfNode(kind=kind, params=merged, transform=transform)


def combine(op: str, *children: SdfNode) -> SdfNode:
    """Build a combinator node folding the child trees."""
    return SdfNode(kind=op, children=list(children))


def bound_box(
    half_extents: tuple[float, float, float],
    *,
    position: tuple[float, float, float] | None = None,
    rotation: tuple[tuple[float, float, float], float] | None = None,
) -> SdfNode:
    """Build a finite clip box (``bound``) for an infinite entity."""
    transform = _make_transform(position=position, rotation=rotation)
    return SdfNode(
        kind="bound",
        params={"halfExtents": list(half_extents)},
        transform=transform,
    )


def _make_transform(
    *,
    position: tuple[float, float, float] | None = None,
    rotation: tuple[tuple[float, float, float], float] | None = None,
) -> dict[str, Any] | None:
    """Build a transform dict, omitting identity components (returns ``None``
    when both position and rotation are absent/identity)."""
    if position is None and rotation is None:
        return None
    transform: dict[str, Any] = {}
    if position is not None:
        transform["position"] = list(position)
    if rotation is not None:
        axis, angle = rotation
        transform["rotation"] = {"axis": list(axis), "angle": float(angle)}
    return transform or None