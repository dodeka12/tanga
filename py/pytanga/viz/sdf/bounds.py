# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Conservative AABB computation for SDF primitive trees.

Walks an :class:`~pytanga.viz.sdf.primitives.SdfNode` tree and returns the
axis-aligned bounding box containing every primitive, accounting for each
node's local ``transform`` (position + axis-angle rotation). The box is
intentionally conservative: any over-estimate is safe (the proxy volume only
needs to *contain* the surface), while under-estimates clip the surface.
"""

from __future__ import annotations

import math
from typing import Any

from .primitives import SdfNode

# Primitive kinds with no finite extent along at least one axis. They only
# become drawable inside a surrounding ``intersect`` / ``bound`` clip, which is
# what actually bounds them.
_UNBOUNDED_PRIMITIVES = {"cylinder", "cone", "plane"}


def compute_bounds(tree: SdfNode, *, padding: float = 0.0) -> dict[str, list[float]]:
    """Return ``{"min": [x,y,z], "max": [x,y,z]}`` bounding *tree*.

    The box is the union over all primitives of their (transformed) local
    boxes, inflated by ``padding`` on every side. Combinators are folded as
    ``union`` (union of children), ``intersect`` (intersection of children),
    ``subtract`` (first child), and ``group`` (conservative union of children).
    """
    box = _bounds_of(tree)
    if box is None:
        box = ([0.0, 0.0, 0.0], [0.0, 0.0, 0.0])
    lo, hi = box
    return {
        "min": [lo[0] - padding, lo[1] - padding, lo[2] - padding],
        "max": [hi[0] + padding, hi[1] + padding, hi[2] + padding],
    }


def _bounds_of(node: SdfNode) -> tuple[list[float], list[float]] | None:
    """Return ``(lo, hi)`` for *node*, or ``None`` when unbounded."""
    kind = node.kind
    children = node.children or []

    if kind in ("union", "group", "xor"):
        lo = [math.inf, math.inf, math.inf]
        hi = [-math.inf, -math.inf, -math.inf]
        for child in children:
            cb = _bounds_of(child)
            if cb is None:
                return None  # a union with an unbounded child is unbounded
            _union_into(lo, hi, cb)
        if math.isinf(lo[0]):
            return None
        return (lo, hi)

    if kind == "intersect":
        lo: list[float] | None = None
        hi: list[float] | None = None
        for child in children:
            cb = _bounds_of(child)
            if cb is None:
                continue  # unbounded child does not constrain the intersection
            if lo is None:
                lo, hi = list(cb[0]), list(cb[1])
            else:
                for i in range(3):
                    lo[i] = max(lo[i], cb[0][i])
                    hi[i] = min(hi[i], cb[1][i])
        if lo is None:
            return None
        return (lo, hi)

    if kind == "subtract":
        if not children:
            return None
        return _bounds_of(children[0])

    # Primitive leaf.
    box = _primitive_box(node)
    if box is None:
        return None
    return _transform_box(box[0], box[1], node.transform)


def _union_into(
    lo: list[float], hi: list[float], box: tuple[list[float], list[float]]
) -> None:
    clo, chi = box
    for i in range(3):
        lo[i] = min(lo[i], clo[i])
        hi[i] = max(hi[i], chi[i])


def _primitive_box(node: SdfNode) -> tuple[list[float], list[float]] | None:
    """Return the local-space ``(lo, hi)`` of a primitive, or ``None`` if unbounded."""
    kind = node.kind
    p = node.params or {}

    if kind == "sphere":
        r = float(p["radius"])
        return ([-r, -r, -r], [r, r, r])
    if kind == "ellipsoid":
        rx, ry, rz = (float(v) for v in p["radii"])
        return ([-rx, -ry, -rz], [rx, ry, rz])
    if kind in ("box", "bound"):
        hx, hy, hz = (float(v) for v in p["halfExtents"])
        return ([-hx, -hy, -hz], [hx, hy, hz])
    if kind == "roundBox":
        hx, hy, hz = (float(v) for v in p["halfExtents"])
        r = float(p["radius"])
        return ([-hx - r, -hy - r, -hz - r], [hx + r, hy + r, hz + r])
    if kind == "cappedCylinder":
        hh = float(p["halfHeight"])
        r = float(p["radius"])
        return ([-r, -hh, -r], [r, hh, r])
    if kind in ("partialDisk", "regularPolygon"):
        # Both are slabs of circumradius `radius` and half-height `halfHeight`
        # lying in the XZ plane; the full circumscribed disk is a conservative
        # (and angle-independent) bound.
        hh = float(p["halfHeight"])
        r = float(p["radius"])
        return ([-r, -hh, -r], [r, hh, r])
    if kind == "cappedCone":
        hh = float(p["halfHeight"])
        r = max(float(p["radius1"]), float(p["radius2"]))
        return ([-r, -hh, -r], [r, hh, r])
    if kind == "torus":
        big = float(p["mainRadius"]) + float(p["tubeRadius"])
        r = float(p["tubeRadius"])
        return ([-big, -r, -big], [big, r, big])
    if kind == "capsule":
        a = p["a"]
        b = p["b"]
        r = max(float(p.get("radiusA", 0.0)), float(p.get("radiusB", 0.0)))
        return (
            [min(a[i], b[i]) - r for i in range(3)],
            [max(a[i], b[i]) + r for i in range(3)],
        )
    if kind == "segment":
        a = p["a"]
        b = p["b"]
        return (
            [min(a[i], b[i]) for i in range(3)],
            [max(a[i], b[i]) for i in range(3)],
        )
    if kind in _UNBOUNDED_PRIMITIVES:
        return None
    raise ValueError(f"Unknown SDF primitive kind {kind!r}")


def _transform_box(
    lo: list[float], hi: list[float], transform: dict[str, Any] | None
) -> tuple[list[float], list[float]]:
    """Apply a node's ``transform`` (position + axis-angle rotation) to a box.

    Returns the axis-aligned bounding box of the 8 transformed corners.
    """
    if not transform:
        return (list(lo), list(hi))
    position = transform.get("position", [0.0, 0.0, 0.0])
    rotation = transform.get("rotation")
    corners = [
        (x, y, z)
        for x in (lo[0], hi[0])
        for y in (lo[1], hi[1])
        for z in (lo[2], hi[2])
    ]
    if rotation:
        axis = rotation["axis"]
        angle = float(rotation["angle"])
        corners = [_rotate(axis, angle, c) for c in corners]
    shifted = [
        (c[0] + position[0], c[1] + position[1], c[2] + position[2])
        for c in corners
    ]
    return (
        [min(c[i] for c in shifted) for i in range(3)],
        [max(c[i] for c in shifted) for i in range(3)],
    )


def _rotate(
    axis: list[float], angle: float, p: tuple[float, float, float]
) -> tuple[float, float, float]:
    """Rotate 3-vector ``p`` about unit-``axis`` by ``angle`` (Rodrigues)."""
    x, y, z = axis
    n = math.sqrt(x * x + y * y + z * z)
    if n < 1e-12:
        return p
    x, y, z = x / n, y / n, z / n
    c = math.cos(angle)
    s = math.sin(angle)
    c1 = 1.0 - c
    px, py, pz = p
    return (
        (c + x * x * c1) * px + (x * y * c1 - z * s) * py + (x * z * c1 + y * s) * pz,
        (y * x * c1 + z * s) * px + (c + y * y * c1) * py + (y * z * c1 - x * s) * pz,
        (z * x * c1 - y * s) * px + (z * y * c1 + x * s) * py + (c + z * z * c1) * pz,
    )

