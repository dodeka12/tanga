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

__all__ = ["Combine", "ECompose", "SdfElement"]


class ECompose(StrEnum):
    """Combine/compose modes for SDF objects.

    Members are string-compatible (``ECompose.SUBTRACT == "subtract"``) so they
    interoperate with the legacy string modes used by ``Composed``/``SdfGroup``.

    ``UNION``/``INTERSECTION``/``SUBTRACT`` double as ordered-fold modes;
    ``XOR`` (symmetric difference) is binary-only and cannot be a fold mode.
    """

    UNION = "union"
    INTERSECTION = "intersection"
    SUBTRACT = "subtract"
    XOR = "xor"


#: Map an ``ECompose`` mode to the GLSL combinator kind used by
#: ``primitives.combine`` (note: the combinator kind spells it ``intersect``,
#: while the fold mode spells it ``intersection``).
_COMBINE_KIND = {
    ECompose.UNION: "union",
    ECompose.INTERSECTION: "intersect",
    ECompose.SUBTRACT: "subtract",
    ECompose.XOR: "xor",
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
class SdfElement:
    """Base class for SDF drawables: a combine mode + operator composition.

    Subclasses (``SdfObject``, ``Combine``, ``Composed``, ``SdfGroup``) inherit
    the operator overloads below, so every SDF drawable composes uniformly.
    """

    combine: ECompose = ECompose.UNION

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


@dataclass(frozen=True, init=False)
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
    ) -> None:
        object.__setattr__(self, "op", op)
        object.__setattr__(self, "a", a)
        object.__setattr__(self, "b", b)
        object.__setattr__(self, "combine", combine)

    def to_sdf_node(self) -> Any:
        from .primitives import combine

        return combine(_COMBINE_KIND[self.op], self.a.to_sdf_node(), self.b.to_sdf_node())


def _coerce(obj: Any) -> SdfElement:
    """Coerce an operand to an ``SdfElement``.

    ``SdfElement`` operands pass through; geometry entities are wrapped in an
    ``SdfObject`` (default style). ``None`` and other types raise.
    """
    if isinstance(obj, SdfElement):
        return obj

    from pytanga.geometry.entities import Cylinder, Entity as GeoEntity

    from .object import SdfObject

    if isinstance(obj, GeoEntity) or isinstance(obj, Cylinder):
        return SdfObject(obj)
    raise TypeError(
        f"Cannot combine {type(obj).__name__} with an SdfElement; "
        "wrap it in SdfObject first"
    )


def _with_combine(el: SdfElement, mode: ECompose) -> SdfElement:
    """Return a shallow copy of *el* with its ``combine`` mode set to *mode*."""
    obj = copy.copy(el)
    object.__setattr__(obj, "combine", mode)
    return obj
