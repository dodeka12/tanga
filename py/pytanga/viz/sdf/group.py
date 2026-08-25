# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Grouped SDF drawable with independently-transformable members.

An :class:`SdfGroup` bundles several SDF members into a single scene object
whose members are rendered as **one** ray-marched solid (so cross-object CSG,
smooth shading, and self-shadowing work across members), yet each member keeps
its own runtime transform so it can be animated independently without
recompiling the shader.

Member transforms are uploaded as shader uniforms and the proxy bounding box is
the union of the members' AABBs, updated dynamically as members move (see the
frontend ``createSdfProxy``/``updateSdfProxy``).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from pytanga.viz._types import TransformRotation, Triple, Vec3, _as_euler, _as_vec3

_COMBINE_MODES = ("union", "intersection", "subtract")


@dataclass
class SdfGroup:
    """A grouped SDF object with per-member combine modes + runtime transforms.

    Each part is either a bare object (defaults to ``"union"``) or an
    ``(object, combine_mode)`` pair. ``object`` may be a geometry entity, an
    operator, a :class:`~pytanga.viz.sdf.primitives.SdfNode`, or a
    :class:`~pytanga.viz.sdf.composed.Composed`.

    Example::

        SdfGroup(sphere(1.0), (capped_cylinder(0.6, 0.4), "subtract"))
    """

    parts: tuple[tuple[Any, str], ...] = ()
    transforms: dict[int, dict[str, Any]] = field(default_factory=dict)
    on_change: Callable[[], None] | None = field(
        default=None, init=False, repr=False, compare=False
    )

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
        self.parts = tuple(normalized)
        self.transforms = {}
        self.on_change = None

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

