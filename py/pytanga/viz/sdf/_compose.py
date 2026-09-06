# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""SDF composition model: ``ECompose``, ``SdfElement`` (operators), ``Combine``.

This is the operator/combine layer over the low-level ``SdfNode`` descriptor.
It lets CSG read as arithmetic:

- ``+`` / ``|`` → union, ``-`` → subtract, ``&`` → intersection, ``^`` → xor.
- unary ``-x`` tags *x* with ``SUBTRACT``; ``~x`` tags it with ``INTERSECTION``
  (the polarity used for ordered-fold membership in ``Composed``/``SdfGroup``).
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

__all__ = ["Combine", "ECompose", "SdfCompose", "SdfElement"]


class ECompose(StrEnum):
    """Combine/compose modes for SDF objects.

    Members are string-compatible (``ECompose.SUBTRACT == "subtract"``) so they
    interoperate with the legacy string modes used by ``Composed``/``SdfGroup``.

    ``UNION``/``INTERSECTION``/``SUBTRACT`` (and their ``SMOOTH_*`` variants)
    double as ordered-fold modes; ``XOR`` (symmetric difference) is binary-only
    and cannot be a fold mode.
    """

    UNION = "union"
    INTERSECTION = "intersection"
    SUBTRACT = "subtract"
    XOR = "xor"
    SMOOTH_UNION = "smooth_union"
    SMOOTH_INTERSECTION = "smooth_intersection"
    SMOOTH_SUBTRACT = "smooth_subtract"


#: Map an ``ECompose`` mode to the GLSL combinator kind used by
#: ``primitives.combine`` (note: the hard combinator kind spells it
#: ``intersect``, while the fold mode spells it ``intersection``).
_COMBINE_KIND = {
    ECompose.UNION: "union",
    ECompose.INTERSECTION: "intersect",
    ECompose.SUBTRACT: "subtract",
    ECompose.XOR: "xor",
    ECompose.SMOOTH_UNION: "smooth_union",
    ECompose.SMOOTH_INTERSECTION: "smooth_intersection",
    ECompose.SMOOTH_SUBTRACT: "smooth_subtract",
}


def _coerce_mode(value: Any, *, allow_xor: bool = False) -> ECompose:
    """Coerce a combine mode (``ECompose`` or legacy string) to an ``ECompose``.

    XOR is rejected unless ``allow_xor`` is True (a binary ``Combine`` context).
    """
    if isinstance(value, ECompose):
        mode = value
    elif isinstance(value, str):
        try:
            mode = ECompose(value)
        except ValueError:
            raise ValueError(f"Unknown combine mode {value!r}") from None
    else:
        raise TypeError(
            f"Combine mode must be an ECompose or str, got {type(value).__name__}"
        )
    if mode is ECompose.XOR and not allow_xor:
        raise ValueError("XOR is a binary-only combine mode, not a fold mode")
    return mode


@dataclass(frozen=True)
class SdfCompose:
    """A tagged member for ``Composed``/``SdfGroup``.

    Binds an element to a fold ``mode`` (``ECompose``) with an optional
    ``smoothness`` blend radius — the named, self-documenting replacement for
    the legacy ``(element, mode[, smoothness])`` tuple form. ``element`` is
    whatever :func:`_coerce` accepts (an ``SdfElement``/``SdfNode``, a geometry
    entity, or a raw multivector).
    """

    element: Any
    mode: ECompose = ECompose.UNION
    smoothness: float | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "mode", _coerce_mode(self.mode))
        if self.smoothness is not None:
            object.__setattr__(self, "smoothness", float(self.smoothness))


@dataclass
class SdfElement:
    """Base class for SDF drawables: a combine mode + operator composition.

    Subclasses (``SdfObject``, ``Combine``, ``Composed``, ``SdfGroup``) inherit
    the operator overloads below, so every SDF drawable composes uniformly.
    """

    combine: ECompose = ECompose.UNION
    smoothness: float | None = None

    # ── Unary polarity (ordered-fold membership) ───────────

    def __neg__(self) -> "SdfElement":
        return _with_combine(self, ECompose.SUBTRACT)

    def __invert__(self) -> "SdfElement":
        return _with_combine(self, ECompose.INTERSECTION)

    # ── Binary composition ─────────────────────────────────

    def __add__(self, other: Any) -> "Combine":
        return Combine(ECompose.UNION, self, _coerce(other))

    def __sub__(self, other: Any) -> "Combine":
        return Combine(ECompose.SUBTRACT, self, _coerce(other))

    def __and__(self, other: Any) -> "Combine":
        return Combine(ECompose.INTERSECTION, self, _coerce(other))

    def __or__(self, other: Any) -> "Combine":
        return Combine(ECompose.UNION, self, _coerce(other))

    def __xor__(self, other: Any) -> "Combine":
        return Combine(ECompose.XOR, self, _coerce(other))

    # ── Reflected binary (raw entity on the left) ──────────

    def __radd__(self, other: Any) -> "Combine":
        return Combine(ECompose.UNION, _coerce(other), self)

    def __rsub__(self, other: Any) -> "Combine":
        return Combine(ECompose.SUBTRACT, _coerce(other), self)

    def __rand__(self, other: Any) -> "Combine":
        return Combine(ECompose.INTERSECTION, _coerce(other), self)

    def __ror__(self, other: Any) -> "Combine":
        return Combine(ECompose.UNION, _coerce(other), self)

    def __rxor__(self, other: Any) -> "Combine":
        return Combine(ECompose.XOR, _coerce(other), self)

    # ── Lowering ───────────────────────────────────────────

    def to_sdf_node(self) -> Any:
        """Lower to a low-level ``SdfNode`` tree (subclasses implement)."""
        raise NotImplementedError(
            f"{type(self).__name__}.to_sdf_node() is not implemented"
        )


@dataclass(init=False)
class Combine(SdfElement):
    """A binary CSG node ``op(a, b)``, produced by the arithmetic operators."""

    op: ECompose
    a: SdfElement
    b: SdfElement

    def __init__(
        self,
        op: ECompose,
        a: SdfElement,
        b: SdfElement,
        *,
        combine: ECompose = ECompose.UNION,
        smoothness: float | None = None,
    ) -> None:
        object.__setattr__(self, "op", op)
        object.__setattr__(self, "a", a)
        object.__setattr__(self, "b", b)
        object.__setattr__(self, "combine", combine)
        object.__setattr__(self, "smoothness", smoothness)

    def to_sdf_node(self) -> Any:
        from .primitives import combine

        return combine(
            _COMBINE_KIND[self.op],
            self.a.to_sdf_node(),
            self.b.to_sdf_node(),
            smoothness=self.smoothness,
        )


def _resolve_mv(obj: Any) -> Any:
    """Resolve a raw multivector to a geometry entity/operator (else unchanged)."""
    from pytanga.algebra import MV

    if isinstance(obj, MV):
        from pytanga.geometry import analyze

        resolved = analyze(obj)
        if resolved is None:
            raise TypeError(f"Could not analyze object: {obj!r}")
        return resolved
    return obj


def _coerce(obj: Any) -> Any:
    """Coerce an operand/member to an SDF element (``SdfElement`` or ``SdfNode``).

    ``SdfElement``/``SdfNode`` pass through; geometry entities are wrapped in an
    ``SdfObject`` (default style); raw multivectors are analyzed first. ``None``
    and other types raise.
    """
    if isinstance(obj, SdfElement):
        return obj

    obj = _resolve_mv(obj)

    from pytanga.geometry.entities import Cylinder, Entity as GeoEntity

    from .object import SdfObject
    from .primitives import SdfNode

    if isinstance(obj, SdfNode):
        return obj
    if isinstance(obj, GeoEntity) or isinstance(obj, Cylinder):
        return SdfObject(obj)
    raise TypeError(
        f"Cannot use {type(obj).__name__} as an SDF element; "
        "wrap it in SdfObject first"
    )


def _normalize_part(part: Any) -> tuple[Any, ECompose]:
    """Normalize a ``Composed``/``SdfGroup`` part to ``(element, fold_mode)``.

    Accepts a bare element (its own ``combine`` is the mode), a unary-tagged
    element (``-el``/``~el``), an :class:`SdfCompose` descriptor, or the legacy
    ``(obj, mode)`` / ``(obj, mode, smoothness)`` tuple/string. Any
    ``smoothness`` is stamped onto the returned element.
    """
    if isinstance(part, SdfCompose):
        element = _coerce(part.element)
        mode = part.mode  # already coerced/validated at construction
        smoothness = part.smoothness
    elif (
        isinstance(part, tuple)
        and len(part) >= 2
        and isinstance(part[1], (ECompose, str))
    ):
        element = _coerce(part[0])
        mode = _coerce_mode(part[1])
        smoothness = part[2] if len(part) == 3 else None
    else:
        element = _coerce(part)
        mode = element.combine if isinstance(element, SdfElement) else ECompose.UNION
        smoothness = getattr(element, "smoothness", None)

    if smoothness is not None:
        element = _stamp_smoothness(element, float(smoothness))
    return element, mode


def _stamp_smoothness(element: Any, smoothness: float) -> Any:
    """Return a shallow copy of *element* with its ``smoothness`` set."""
    obj = copy.copy(element)
    object.__setattr__(obj, "smoothness", smoothness)
    return obj


def _with_combine(el: SdfElement, mode: ECompose) -> SdfElement:
    """Return a shallow copy of *el* with its ``combine`` mode set to *mode*."""
    obj = copy.copy(el)
    object.__setattr__(obj, "combine", mode)
    return obj
