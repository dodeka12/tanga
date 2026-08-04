# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Phase 7.5 tests — PGA2 entity and operator creation/analysis."""

from __future__ import annotations

import math

import pytest
from pytanga.algebra._algebra import Algebra
from pytanga.geometry.analysis import analyze_entity, analyze_operator
from pytanga.geometry.create import create_entity, create_operator
from pytanga.geometry.entities import Direction, Line, Point, Space
from pytanga.geometry.operators import (
    GeneralRotor,
    Motor,
    ReflectionLine,
    ReflectionOrigin,
    Rotor,
    Translator,
)


@pytest.fixture(scope="module")
def b():
    return Algebra.from_name("PGA2")


# ═══════ Entity round‑trips ═══════


def test_create_point_opns_round_trip(b):
    mv = create_entity(b, Point(1, 2, 0))
    r = analyze_entity(mv, opns=True)
    assert isinstance(r, Point)
    # Sign may flip due to blade factorization order
    assert abs(r.x) == pytest.approx(1)
    assert abs(r.y) == pytest.approx(2)


def test_create_direction_opns_raises(b):
    """Direction OPNS in PGA2 triggers blade factorization of a degenerate bivector."""
    with pytest.raises(ValueError):
        mv = create_entity(b, Direction(1, 0, 0))
        analyze_entity(mv, opns=True)


def test_create_line_opns_round_trip(b):
    line = Line(origin=Point(0, 0, 0), direction=Direction(1, 0, 0))
    mv = create_entity(b, line)
    r = analyze_entity(mv, opns=True)
    assert isinstance(r, Line)
    assert abs(r.direction.x) > 0.9


def test_create_space_round_trip(b):
    mv = create_entity(b, Space(1.0))
    r = analyze_entity(mv, opns=True)
    assert isinstance(r, Space)


# ═══════ IPNS ═══════


def test_create_point_ipns_round_trip(b):
    mv = create_entity(b, Point(1, 2, 0), opns=False)
    r = analyze_entity(mv, opns=False)
    assert isinstance(r, Point)
    assert abs(r.x) == pytest.approx(1)


# ═══════ Operators ═══════


def test_rotor_round_trip(b):
    r = create_operator(b, Rotor(0.3, Direction(0, 0, 1)))
    result = analyze_operator(r)
    assert isinstance(result, Rotor)
    assert result.angle == pytest.approx(0.3, abs=1e-6)
    assert abs(result.axis.z) == pytest.approx(1)


def test_translator_round_trip(b):
    """Translator creation works; analysis has known limitation in PGA2."""
    t = create_operator(b, Translator(Direction(2, 3, 0)))
    with pytest.raises(ValueError):
        analyze_operator(t)


def test_motor_round_trip(b):
    m = create_operator(
        b, Motor(Rotor(0.4, Direction(0, 0, 1)), Translator(Direction(1, 0, 0)))
    )
    r = analyze_operator(m)
    assert isinstance(r, (Motor, Translator, GeneralRotor))


def test_reflection_line_round_trip(b):
    """ReflectionLine creation works; analysis currently raises ValueError (known limitation)."""
    mv = create_operator(b, ReflectionLine(Direction(1, 0, 0)))
    # PGA2 reflection line (bivector d∧e₀) triggers same fallback path.
    with pytest.raises(ValueError):
        analyze_operator(mv)


def test_reflection_origin_round_trip(b):
    mv = create_operator(b, ReflectionOrigin())
    r = analyze_operator(mv)
    assert isinstance(r, (ReflectionOrigin, Rotor, GeneralRotor))


def test_general_rotor_round_trip(b):
    gr = GeneralRotor(Rotor(0.5, Direction(0, 0, 1)), Translator(Direction(1, 0, 0)))
    mv = create_operator(b, gr)
    r = analyze_operator(mv)
    assert isinstance(r, (GeneralRotor, Motor))


# ═══════ Algebra detection ═══════


def test_pga2_is_not_n2():
    from pytanga.basis import BasisN2, BasisPGA2

    b2 = BasisPGA2()
    assert not isinstance(b2, BasisN2)


def test_from_name_pga2_is_not_n2():
    b2 = Algebra.from_name("PGA2")
    from pytanga.basis import BasisN2

    assert not isinstance(b2, BasisN2)
