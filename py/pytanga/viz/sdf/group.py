# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Grouped SDF drawable with independently-transformable members.

An :class:`SdfGroup` bundles several SDF members into a single scene object
whose members are rendered as **one** ray-marched solid (so cross-object CSG,
smooth shading, and self-shadowing work across members), yet each member keeps
its own runtime transform so it can be animated independently without
recompiling the shader.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any, Callable

from pytanga.viz._types import TransformRotation, Triple, Vec3, _as_euler, _as_vec3

from ._compose import ECompose, SdfElement, _normalize_part
from .composed import _member_node
from .primitives import SdfNode, group


@dataclass(init=False)
class SdfGroup(SdfElement):
    """A grouped SDF object with per-member combine modes + runtime transforms.

    Each part is a bare element (defaults to union), a unary-tagged element
    (``-el`` / ``~el``), or a legacy ``(obj, mode)`` tuple/string. ``obj`` may be
    a geometry entity, an ``SdfNode``, an ``SdfObject``/``Combine``, or a nested
    ``Composed``/``SdfGroup``.

    Example::

        SdfGroup(sphere(1.0), (capped_cylinder(0.6, 0.4), "subtract"))
    """

    parts: tuple[tuple[Any, ECompose], ...]
    transforms: dict[int, dict[str, Any]] = field(default_factory=dict)
    on_change: Callable[[], None] | None = field(
        default=None, init=False, repr=False, compare=False
    )

    def __init__(
        self,
        *parts: Any,
        combine: ECompose = ECompose.UNION,
        smoothness: float | None = None,
    ) -> None:
        self.parts = tuple(_normalize_part(p) for p in parts)
        self.transforms = {}
        self.on_change = None
        self.combine = combine
        self.smoothness = smoothness

    # ── Member addressing ─────────────────────────────────────

    @property
    def member_ids(self) -> list[str | None]:
        """The optional id of each member (``None`` for unnamed members)."""
        return [getattr(obj, "id", None) for obj, _ in self.parts]

    def _resolve_member_index(self, member: int | str) -> int:
        """Resolve a member reference (int index or str id) to an index."""
        if isinstance(member, int):
            if 0 <= member < len(self.parts):
                return member
            raise IndexError(
                f"Member index {member} out of range for {len(self.parts)} members"
            )
        if isinstance(member, str):
            for index, (obj, _) in enumerate(self.parts):
                if getattr(obj, "id", None) == member:
                    return index
            raise KeyError(f"No group member named {member!r}")
        raise TypeError(
            f"Member must be an int index or a str id, got {type(member).__name__}"
        )

    def set_member_transform(
        self,
        member: int | str,
        *,
        position: Vec3 = None,
        rotation: TransformRotation = None,
        scale: Triple = None,
    ) -> None:
        """Override a member's runtime transform (absolute, group-local).

        *member* is either the member's 0-based index or its ``id``. Only the
        provided components are changed; unset components keep their previous
        value (or the member's intrinsic placement). ``rotation`` is an Euler
        triple or a Rotor (converted to Euler).
        """
        index = self._resolve_member_index(member)
        transform = self.transforms.setdefault(index, {})
        if position is not None:
            transform["position"] = list(_as_vec3(position))
        if rotation is not None:
            transform["rotation"] = list(_as_euler(rotation))
        if scale is not None:
            transform["scale"] = list(_as_vec3(scale))
        if self.on_change is not None:
            self.on_change()

    # ── Lowering (fixed-tree snapshot, used when nested) ──────

    def to_sdf_node(self) -> SdfNode:
        children: list[SdfNode] = []
        for element, mode in self.parts:
            child = copy.copy(_member_node(element))
            child.combine = mode.value
            child.smoothness = getattr(element, "smoothness", None)
            children.append(child)
        return group(children)


