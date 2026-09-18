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
    Circle,
    Direction,
    Geometry,
    HDirection,
    HPoint,
    Line,
    Plane,
    Point,
    PointPair,
    Space,
    Sphere,
)
from pytanga.geometry.operators import (
    Dilator,
    GeneralRotor,
    Inversion,
    Motor,
    ReflectionLine,
    ReflectionPlane,
    ReflectionPoint,
    Rotor,
    Translator,
    TwistBivector,
)
from pytanga.geometry.mask import mask_for


def assert_mask_basis(alg, typ, expected_names):  # noqa: ANN001, ANN201
    """Assert ``mask_for(alg, typ)`` carries exactly *expected_names*."""
    mask = mask_for(alg, typ)
    assert mask.basis_names == expected_names, (
        f"{typ.__name__}: expected {expected_names}, got {mask.basis_names}"
    )


def test_e2_mask_named_basis():  # noqa: ANN201
    alg = BasisE2()
    assert_mask_basis(alg, Point, ["e1", "e2"])
    assert_mask_basis(alg, Direction, ["e1", "e2"])
    assert_mask_basis(alg, Space, ["I"])
    assert_mask_basis(alg, Rotor, ["s", "I"])
    assert_mask_basis(alg, ReflectionLine, ["e1", "e2"])


def test_e3_mask_named_basis():  # noqa: ANN201
    alg = BasisE3()
    assert_mask_basis(alg, Point, ["e1", "e2", "e3"])
    assert_mask_basis(alg, Direction, ["e1", "e2", "e3"])
    assert_mask_basis(alg, Space, ["I"])
    assert_mask_basis(alg, Rotor, ["s", "e12", "e13", "e23"])
    assert_mask_basis(alg, ReflectionPlane, ["e12", "e13", "e23"])
    assert_mask_basis(alg, ReflectionLine, ["e1", "e2", "e3"])


def test_p2_mask_named_basis():  # noqa: ANN201
    alg = BasisP2()
    assert_mask_basis(alg, Point, ["e1", "e2", "e3"])
    assert_mask_basis(alg, Direction, ["e1", "e2"])
    assert_mask_basis(alg, Line, ["e12", "e13", "e23"])
    assert_mask_basis(alg, Space, ["I"])
    assert_mask_basis(alg, Rotor, ["s", "e12"])
    assert_mask_basis(alg, ReflectionLine, ["e13", "e23"])
    assert_mask_basis(alg, ReflectionPoint, ["e1", "e2", "e3"])


def test_p3_mask_named_basis():  # noqa: ANN201
    alg = BasisP3()
    assert_mask_basis(alg, Point, ["e1", "e2", "e3", "e4"])
    assert_mask_basis(alg, Direction, ["e1", "e2", "e3"])
    assert_mask_basis(alg, Line, ["e12", "e13", "e14", "e23", "e24", "e34"])
    assert_mask_basis(alg, Plane, ["e123", "e124", "e134", "e234"])
    assert_mask_basis(alg, Space, ["I"])
    assert_mask_basis(alg, Rotor, ["s", "e12", "e13", "e23"])
    assert_mask_basis(alg, ReflectionPlane, ["e1", "e2", "e3"])
    assert_mask_basis(alg, ReflectionLine, ["e14", "e24", "e34"])
    assert_mask_basis(alg, ReflectionPoint, ["e1", "e2", "e3", "e4"])


def test_n2_mask_named_basis():  # noqa: ANN201
    alg = BasisN2()
    assert_mask_basis(alg, Point, ["e1", "e2", "einf", "eo"])
    assert_mask_basis(alg, Direction, ["e1", "e2"])
    assert_mask_basis(alg, Line, ["e12∧einf", "e12∧eo", "e1∧einf∧eo", "e2∧einf∧eo"])
    assert_mask_basis(alg, Sphere, ["e12∧einf", "e12∧eo", "e1∧einf∧eo", "e2∧einf∧eo"])
    assert_mask_basis(alg, Circle, ["e12∧einf", "e12∧eo", "e1∧einf∧eo", "e2∧einf∧eo"])
    assert_mask_basis(
        alg,
        PointPair,
        ["e12", "e1∧einf", "e1∧eo", "e2∧einf", "e2∧eo", "einf∧eo"],
    )
    assert_mask_basis(alg, HPoint, ["e1∧einf", "e1∧eo", "e2∧einf", "e2∧eo", "einf∧eo"])
    assert_mask_basis(alg, HDirection, ["e1∧einf", "e1∧eo", "e2∧einf", "e2∧eo"])
    assert_mask_basis(alg, Space, ["I"])
    assert_mask_basis(alg, Rotor, ["s", "e12"])
    assert_mask_basis(alg, Translator, ["s", "e1∧einf", "e1∧eo", "e2∧einf", "e2∧eo"])
    assert_mask_basis(alg, Motor, ["s", "e12", "e1∧einf", "e1∧eo", "e2∧einf", "e2∧eo"])
    assert_mask_basis(
        alg, Dilator, ["s", "e1∧einf", "e1∧eo", "e2∧einf", "e2∧eo", "einf∧eo"]
    )
    assert_mask_basis(alg, Inversion, ["e1", "e2", "einf", "eo"])
    assert_mask_basis(
        alg, ReflectionLine, ["e12∧einf", "e12∧eo", "e1∧einf∧eo", "e2∧einf∧eo"]
    )
    assert_mask_basis(
        alg, ReflectionPoint, ["e1∧einf", "e1∧eo", "e2∧einf", "e2∧eo", "einf∧eo"]
    )
    assert_mask_basis(alg, GeneralRotor, ["s", "e12", "e1∧einf", "e1∧eo", "e2∧einf", "e2∧eo"])


def test_n3_mask_named_basis():  # noqa: ANN201
    alg = BasisN3()
    assert_mask_basis(alg, Point, ["e1", "e2", "e3", "einf", "eo"])
    assert_mask_basis(alg, Direction, ["e1", "e2", "e3"])
    assert_mask_basis(
        alg,
        Line,
        ["e12∧einf", "e12∧eo", "e13∧einf", "e13∧eo", "e1∧einf∧eo", "e23∧einf", "e23∧eo", "e2∧einf∧eo", "e3∧einf∧eo"],
    )
    assert_mask_basis(
        alg, Plane, ["e123∧einf", "e123∧eo", "e12∧einf∧eo", "e13∧einf∧eo", "e23∧einf∧eo"]
    )
    assert_mask_basis(
        alg, Sphere, ["e123∧einf", "e123∧eo", "e12∧einf∧eo", "e13∧einf∧eo", "e23∧einf∧eo"]
    )
    assert_mask_basis(
        alg,
        Circle,
        ["e123", "e12∧einf", "e12∧eo", "e13∧einf", "e13∧eo", "e1∧einf∧eo", "e23∧einf", "e23∧eo", "e2∧einf∧eo", "e3∧einf∧eo"],
    )
    assert_mask_basis(
        alg,
        PointPair,
        ["e12", "e13", "e1∧einf", "e1∧eo", "e23", "e2∧einf", "e2∧eo", "e3∧einf", "e3∧eo", "einf∧eo"],
    )
    assert_mask_basis(alg, HPoint, ["e1∧einf", "e1∧eo", "e2∧einf", "e2∧eo", "e3∧einf", "e3∧eo", "einf∧eo"])
    assert_mask_basis(alg, HDirection, ["e1∧einf", "e1∧eo", "e2∧einf", "e2∧eo", "e3∧einf", "e3∧eo"])
    assert_mask_basis(alg, Space, ["I"])
    assert_mask_basis(alg, Rotor, ["s", "e12", "e13", "e23"])
    assert_mask_basis(alg, Translator, ["s", "e1∧einf", "e1∧eo", "e2∧einf", "e2∧eo", "e3∧einf", "e3∧eo"])
    assert_mask_basis(
        alg,
        Motor,
        ["s", "e12", "e13", "e1∧einf", "e1∧eo", "e23", "e2∧einf", "e2∧eo", "e3∧einf", "e3∧eo", "e123∧einf", "e123∧eo"],
    )
    assert_mask_basis(alg, TwistBivector, ["e12", "e13", "e23", "e1∧einf", "e2∧einf", "e3∧einf"])
    assert_mask_basis(alg, Dilator, ["s", "e1∧einf", "e1∧eo", "e2∧einf", "e2∧eo", "e3∧einf", "e3∧eo", "einf∧eo"])
    assert_mask_basis(alg, Inversion, ["e1", "e2", "e3", "einf", "eo"])
    assert_mask_basis(
        alg, ReflectionPlane, ["e123∧einf", "e123∧eo", "e12∧einf∧eo", "e13∧einf∧eo", "e23∧einf∧eo"]
    )
    assert_mask_basis(
        alg,
        ReflectionLine,
        ["e12∧einf", "e12∧eo", "e13∧einf", "e13∧eo", "e1∧einf∧eo", "e23∧einf", "e23∧eo", "e2∧einf∧eo", "e3∧einf∧eo"],
    )
    assert_mask_basis(alg, ReflectionPoint, ["e1∧einf", "e1∧eo", "e2∧einf", "e2∧eo", "e3∧einf", "e3∧eo", "einf∧eo"])
    assert_mask_basis(alg, GeneralRotor, ["s", "e12", "e13", "e23"])


def test_pga2_mask_named_basis():  # noqa: ANN201
    alg = BasisPGA2()
    assert_mask_basis(alg, Point, ["e10", "e20", "e12", "ei1", "ei2"])
    assert_mask_basis(alg, Direction, ["e10", "e20", "ei1", "ei2"])
    assert_mask_basis(alg, Line, ["e0", "e1", "e2", "ei"])
    assert_mask_basis(alg, Space, ["I", "Ii"])
    assert_mask_basis(alg, Rotor, ["s", "e12"])
    assert_mask_basis(alg, Translator, ["s", "e10", "e20", "ei1", "ei2"])
    assert_mask_basis(alg, Motor, ["s", "e10", "e20", "e12", "ei1", "ei2"])
    assert_mask_basis(alg, ReflectionLine, ["e0", "e1", "e2", "ei"])
    assert_mask_basis(alg, ReflectionPoint, ["e10", "e20", "e12", "ei1", "ei2"])
    assert_mask_basis(alg, GeneralRotor, ["s", "e10", "e20", "e12", "ei1", "ei2"])


def test_pga3_mask_named_basis():  # noqa: ANN201
    alg = BasisPGA3()
    assert_mask_basis(alg, Point, ["e032", "e013", "e021", "e123", "ei32", "ei13", "ei21"])
    assert_mask_basis(alg, Direction, ["e032", "e013", "e021", "ei32", "ei13", "ei21"])
    assert_mask_basis(alg, Line, ["e01", "e02", "e03", "e23", "e31", "e12", "ei1", "ei2", "ei3"])
    assert_mask_basis(alg, Plane, ["e0", "e1", "e2", "e3", "e0i"])
    assert_mask_basis(alg, Space, ["I", "Ii"])
    assert_mask_basis(alg, Rotor, ["s", "e23", "e31", "e12"])
    assert_mask_basis(alg, Translator, ["s", "e01", "e02", "e03", "ei1", "ei2", "ei3"])
    assert_mask_basis(
        alg,
        Motor,
        ["s", "e01", "e02", "e03", "e23", "e31", "e12", "ei1", "ei2", "ei3", "I", "Ii"],
    )
    assert_mask_basis(alg, ReflectionPlane, ["e0", "e1", "e2", "e3", "e0i"])
    assert_mask_basis(alg, ReflectionLine, ["e01", "e02", "e03", "e23", "e31", "e12", "ei1", "ei2", "ei3"])
    assert_mask_basis(alg, ReflectionPoint, ["e032", "e013", "e021", "e123", "ei32", "ei13", "ei21"])
    assert_mask_basis(alg, GeneralRotor, ["s", "e23", "e31", "e12"])


ALL_ALGS = [BasisE2, BasisE3, BasisP2, BasisP3, BasisN2, BasisN3, BasisPGA2, BasisPGA3]

# (type) -> supported on all algebras above
ALWAYS_SUPPORTED = [
    Point,
    Direction,
    Space,
    Rotor,
]


def test_hardcoded_type_mask_ids():  # noqa: ANN201
    """The hard-coded type masks are full (no partial-template regression)."""
    n2 = Geometry(BasisN2())
    assert n2.mask_for(Sphere).ids == [7, 11, 13, 14]
    assert n2.mask_for(Circle).ids == [7, 11, 13, 14]
    assert n2.mask_for(Inversion).ids == [1, 2, 4, 8]
    assert Geometry(BasisN2(opns=False)).mask_for(Sphere).ids == [1, 2, 4, 8]

    n3 = Geometry(BasisN3())
    assert n3.mask_for(Point).ids == [1, 2, 4, 8, 16]


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
def test_rotor_mask_literal(alg_cls, expected_ids):  # noqa: ANN001, ANN201
    geo = Geometry(alg_cls())
    assert set(geo.mask_for(Rotor).ids) == expected_ids


def test_opns_flips_entity_mask_but_not_operator():  # noqa: ANN201
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


def test_n3_point_opns_is_grade1_and_ipns_is_grade4():  # noqa: ANN201
    alg = BasisN3()
    geo = Geometry(alg)
    assert {b.bit_count() for b in geo.mask_for(Point).ids} == {1}

    alg.opns = False
    assert {b.bit_count() for b in geo.mask_for(Point).ids} == {4}


def test_class_and_instance_give_same_mask_for_generic_instance():  # noqa: ANN201
    geo = Geometry(BasisN3())
    cls_mask = geo.mask_for(Rotor)
    inst_mask = geo.mask_for(Rotor(0.7, Direction(1, 2, 3)))
    assert cls_mask == inst_mask


def test_instance_mask_is_nonzero_blade_subset():  # noqa: ANN201
    # A rotor about the z-axis only has scalar + e12 non-zero; the class mask
    # has all three bivectors.  An instance reflects its actual blades.
    geo = Geometry(BasisE3())
    cls_mask = geo.mask_for(Rotor)
    inst_mask = geo.mask_for(Rotor(0.5, Direction(0, 0, 1)))
    assert set(inst_mask.ids) == {0, 3}
    assert set(cls_mask.ids) == {0, 3, 5, 6}


def test_create_var_returns_variable_with_correct_mask():  # noqa: ANN201
    geo = Geometry(BasisN3())
    v = geo.create_var("R1", Rotor)
    assert isinstance(v, Variable)
    assert v.name == "R1"
    assert v.algebra is geo.algebra
    assert v.mask == geo.mask_for(Rotor)


def test_call_string_form_aliases_create_var():  # noqa: ANN201
    geo = Geometry(BasisN3())
    v = geo("R1", Rotor)
    w = geo.create_var("R1", Rotor)
    assert isinstance(v, Variable)
    assert v.name == w.name == "R1"
    assert v.mask == w.mask


def test_call_plain_dispatch_unchanged():  # noqa: ANN201
    geo = Geometry(BasisN3())
    mv = geo(Point(1, 2, 3))
    assert geo.create(Point(1, 2, 3)).grades == mv.grades


def test_module_level_helpers():  # noqa: ANN201
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
def test_unsupported_types_raise(alg_cls, typ):  # noqa: ANN001, ANN201
    geo = Geometry(alg_cls())
    with pytest.raises((TypeError, ValueError)):
        geo.mask_for(typ)


def test_untyped_containers_raise():  # noqa: ANN201
    from pytanga.geometry.entities import ImagCircle
    from pytanga.geometry.operators import TripleReflection

    geo = Geometry(BasisN3())
    with pytest.raises(TypeError):
        geo.mask_for(ImagCircle)
    with pytest.raises(TypeError):
        geo.mask_for(TripleReflection)


def test_twist_bivector_mask_is_motor_intersect_grade2():  # noqa: ANN201
    geo = Geometry(BasisN3())
    twist = geo.mask_for(TwistBivector)
    expected = geo.mask_for(Motor).intersection(
        BladeMask(geo.algebra, grades=[2])
    )
    assert twist == expected
    assert twist.ids == [3, 5, 6, 9, 10, 12, 17, 18, 20]


def test_twist_bivector_create_var():  # noqa: ANN201
    geo = Geometry(BasisN3())
    v = geo.create_var("T", TwistBivector)
    assert isinstance(v, Variable)
    assert v.name == "T"
    assert v.mask == geo.mask_for(TwistBivector)


def test_twist_bivector_mask_named_basis_6_dof():  # noqa: ANN201
    geo = Geometry(BasisN3())
    twist = geo.mask_for(TwistBivector)
    assert twist.basis_names == [
        "e12",
        "e13",
        "e23",
        "e1∧einf",
        "e2∧einf",
        "e3∧einf",
    ]
    assert len(twist.basis_vectors) == 6
    assert twist.basis_matrix().shape == (9, 6)


@pytest.mark.parametrize(
    "alg_cls",
    [BasisE3, BasisP3, BasisPGA3, BasisN2, BasisE2, BasisP2, BasisPGA2],
)
def test_twist_bivector_unsupported_algebras_raise(alg_cls):  # noqa: ANN001, ANN201
    geo = Geometry(alg_cls())
    with pytest.raises(TypeError):
        geo.mask_for(TwistBivector)
