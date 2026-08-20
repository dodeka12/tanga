# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for Geometry.create_var / mask_for (blade-mask derivation)."""

from __future__ import annotations

import pytest

from pytanga import BladeMask, Variable
from pytanga.basis import (
    BasisE2,
    BasisE3,
    BasisN2,
    BasisN3,
    BasisP2,
    BasisP3,
    BasisPGA2,
    BasisPGA3,
)
from pytanga.geometry import (
    Direction,
    Geometry,
    Point,
    Space,
    Sphere,
)
from pytanga.geometry.operators import (
    Motor,
    Rotor,
    Translator,
)
from pytanga.geometry.mask import _template, mask_for


ALL_ALGS = [BasisE2, BasisE3, BasisP2, BasisP3, BasisN2, BasisN3, BasisPGA2, BasisPGA3]

# (type) -> supported on all algebras above
ALWAYS_SUPPORTED = [
    Point,
    Direction,
    Space,
    Rotor,
]


def test_mask_for_matches_create_for_all_algebras():
    """For every supported type, the mask is exactly the blades of create()."""
    from pytanga.geometry import create

    for alg_cls in ALL_ALGS:
        alg = alg_cls()
        geo = Geometry(alg)
        for typ in ALWAYS_SUPPORTED:
            inst = _template(typ)
            expected = BladeMask(create(alg, inst))
            assert geo.mask_for(typ) == expected, (alg_cls.__name__, typ.__name__)


@pytest.mark.parametrize(
    "alg_cls, expected_ids",
    [
        (BasisE3, {0, 3, 5, 6}),
        (BasisP3, {0, 3, 5, 6}),
        (BasisN3, {0, 3, 5, 6}),
        (BasisPGA3, {0, 3, 5, 6}),
        (BasisE2, {0, 3}),
        (BasisP2, {0, 3}),
        (BasisN2, {0, 3}),
        (BasisPGA2, {0, 3}),
    ],
)
def test_rotor_mask_literal(alg_cls, expected_ids):
    geo = Geometry(alg_cls())
    assert set(geo.mask_for(Rotor).ids) == expected_ids


def test_opns_flips_entity_mask_but_not_operator():
    alg = BasisN3()
    geo = Geometry(alg)

    rotor = geo.mask_for(Rotor)
    opns_point = geo.mask_for(Point)

    alg.opns = False
    ipns_point = geo.mask_for(Point)

    # Rotor is opns-independent
    assert geo.mask_for(Rotor) == rotor
    # Point changes representation (grade-1 OPNS vs grade-4 IPNS)
    assert opns_point != ipns_point


def test_n3_point_opns_is_grade1_and_ipns_is_grade4():
    alg = BasisN3()
    geo = Geometry(alg)
    assert {b.bit_count() for b in geo.mask_for(Point).ids} == {1}

    alg.opns = False
    assert {b.bit_count() for b in geo.mask_for(Point).ids} == {4}


def test_class_and_instance_give_same_mask_for_generic_instance():
    geo = Geometry(BasisN3())
    cls_mask = geo.mask_for(Rotor)
    inst_mask = geo.mask_for(Rotor(0.7, Direction(1, 2, 3)))
    assert cls_mask == inst_mask


def test_instance_mask_is_nonzero_blade_subset():
    # A rotor about the z-axis only has scalar + e12 non-zero; the class mask
    # has all three bivectors.  An instance reflects its actual blades.
    geo = Geometry(BasisE3())
    cls_mask = geo.mask_for(Rotor)
    inst_mask = geo.mask_for(Rotor(0.5, Direction(0, 0, 1)))
    assert set(inst_mask.ids) == {0, 3}
    assert set(cls_mask.ids) == {0, 3, 5, 6}


def test_create_var_returns_variable_with_correct_mask():
    geo = Geometry(BasisN3())
    v = geo.create_var("R1", Rotor)
    assert isinstance(v, Variable)
    assert v.name == "R1"
    assert v.algebra is geo.algebra
    assert v.mask == geo.mask_for(Rotor)


def test_call_string_form_aliases_create_var():
    geo = Geometry(BasisN3())
    v = geo("R1", Rotor)
    w = geo.create_var("R1", Rotor)
    assert isinstance(v, Variable)
    assert v.name == w.name == "R1"
    assert v.mask == w.mask


def test_call_plain_dispatch_unchanged():
    geo = Geometry(BasisN3())
    mv = geo(Point(1, 2, 3))
    assert geo.create(Point(1, 2, 3)).grades == mv.grades


def test_module_level_helpers():
    from pytanga.geometry import create_var, mask_for as public_mask_for

    alg = BasisN3()
    assert public_mask_for(alg, Rotor) == mask_for(alg, Rotor)
    v = create_var(alg, "X", Rotor)
    assert isinstance(v, Variable)
    assert v.name == "X"


@pytest.mark.parametrize(
    "alg_cls, typ",
    [
        (BasisE3, Translator),
        (BasisP3, Translator),
        (BasisE3, Sphere),
        (BasisP3, Sphere),
        (BasisE3, Motor),
    ],
)
def test_unsupported_types_raise(alg_cls, typ):
    geo = Geometry(alg_cls())
    with pytest.raises((TypeError, ValueError)):
        geo.mask_for(typ)


def test_untyped_containers_raise():
    from pytanga.geometry.entities import ImagCircle
    from pytanga.geometry.operators import TripleReflection

    geo = Geometry(BasisN3())
    with pytest.raises(TypeError):
        geo.mask_for(ImagCircle)
    with pytest.raises(TypeError):
        geo.mask_for(TripleReflection)
