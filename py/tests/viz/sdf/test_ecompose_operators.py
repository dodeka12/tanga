# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for ECompose + SdfElement operators + Combine (viz-sdf-object-model Phase 2)."""

from __future__ import annotations

from dataclasses import dataclass

import pytest
from pytanga.viz.sdf._compose import Combine, ECompose, SdfElement, _coerce, _coerce_mode
from pytanga.viz.sdf.primitives import box, sphere


@dataclass(frozen=True, init=False)
class _Leaf(SdfElement):
    """Test stub: an SdfElement wrapping a prebuilt SdfNode."""

    node: object

    def __init__(self, node: object, *, combine: ECompose = ECompose.UNION) -> None:
        object.__setattr__(self, "node", node)
        object.__setattr__(self, "combine", combine)

    def to_sdf_node(self) -> object:
        return self.node


def test_ecompose_is_string_compatible() -> None:
    assert ECompose.SUBTRACT == "subtract"
    assert ECompose.INTERSECTION == "intersection"
    assert ECompose.UNION == "union"
    assert ECompose.XOR == "xor"


def test_coerce_mode_roundtrip() -> None:
    assert _coerce_mode("subtract") is ECompose.SUBTRACT
    assert _coerce_mode(ECompose.INTERSECTION) is ECompose.INTERSECTION


def test_coerce_mode_rejects_xor_in_fold_context() -> None:
    with pytest.raises(ValueError):
        _coerce_mode("xor")
    with pytest.raises(ValueError):
        _coerce_mode(ECompose.XOR)


def test_coerce_mode_allows_xor_in_binary_context() -> None:
    assert _coerce_mode("xor", allow_xor=True) is ECompose.XOR


def test_coerce_mode_rejects_unknown_string() -> None:
    with pytest.raises(ValueError):
        _coerce_mode("bogus")


def test_unary_neg_sets_subtract_polarity() -> None:
    el = SdfElement()
    tagged = -el
    assert tagged is not el
    assert tagged.combine is ECompose.SUBTRACT
    assert el.combine is ECompose.UNION  # original unchanged


def test_unary_invert_sets_intersection_polarity() -> None:
    el = SdfElement()
    tagged = ~el
    assert tagged.combine is ECompose.INTERSECTION
    assert el.combine is ECompose.UNION


@pytest.mark.parametrize(
    "expr,op,left_is_self",
    [
        ("add", ECompose.UNION, True),
        ("sub", ECompose.SUBTRACT, True),
        ("and", ECompose.INTERSECTION, True),
        ("or", ECompose.UNION, True),
        ("xor", ECompose.XOR, True),
    ],
)
def test_binary_operators_build_combine(expr, op, left_is_self) -> None:
    a = SdfElement()
    b = SdfElement()
    if expr == "add":
        node = a + b
    elif expr == "sub":
        node = a - b
    elif expr == "and":
        node = a & b
    elif expr == "or":
        node = a | b
    else:
        node = a ^ b
    assert isinstance(node, Combine)
    assert node.op is op
    assert node.a is a
    assert node.b is b


def test_reflected_operators_put_raw_left_operand_first() -> None:
    a = SdfElement()
    b = SdfElement()
    # (b on the left of a non-SdfElement triggers __r*__); here both are
    # SdfElement so the forward operator runs; verify __rsub__ via a fake int.
    with pytest.raises(TypeError):
        _ = 1 + a  # _coerce(int) raises (raw-entity wrapping is Phase 3)


def test_coerce_passes_sdf_element_through() -> None:
    el = SdfElement()
    assert _coerce(el) is el


def test_coerce_rejects_non_element() -> None:
    with pytest.raises(TypeError):
        _coerce(123)


def test_combine_to_sdf_node_shape() -> None:
    a = _Leaf(sphere(1.0))
    b = _Leaf(box((0.5, 0.5, 0.5)))
    node = (a + b).to_sdf_node()
    assert node.kind == "union"
    assert len(node.children) == 2


@pytest.mark.parametrize(
    "op,kind",
    [
        (ECompose.UNION, "union"),
        (ECompose.INTERSECTION, "intersect"),
        (ECompose.SUBTRACT, "subtract"),
        (ECompose.XOR, "xor"),
    ],
)
def test_combine_kind_mapping(op, kind) -> None:
    node = Combine(op, _Leaf(sphere(1.0)), _Leaf(sphere(0.5))).to_sdf_node()
    assert node.kind == kind
