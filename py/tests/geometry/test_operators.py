# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Christian Perwass

"""Unit tests for operator data classes (Motor screw decomposition)."""

import math

import pytest

from pytanga.basis import BasisN3
from pytanga.geometry.analysis import analyze_operator
from pytanga.geometry.create import create_operator
from pytanga.geometry.entities import Direction, Point
from pytanga.geometry.operators import GeneralRotor, Motor, Rotor, Translator


def test_motor_decomposes_pure_axial():
    """Translation along the axis stays axial; the axis is undisplaced."""
    m = Motor(
        rotor=Rotor(math.pi / 2, Direction(0, 0, 1)),
        translator=Translator(Direction(0, 0, 2)),
    )
    assert isinstance(m.rotor, GeneralRotor)
    assert m.rotor.angle == pytest.approx(math.pi / 2)
    assert m.rotor.origin.x == pytest.approx(0)
    assert m.rotor.origin.y == pytest.approx(0)
    assert m.rotor.origin.z == pytest.approx(0)
    assert m.translator.vector.x == pytest.approx(0)
    assert m.translator.vector.y == pytest.approx(0)
    assert m.translator.vector.z == pytest.approx(2)


def test_motor_decomposes_pure_perpendicular():
    """A perpendicular translation displaces the axis (no axial component)."""
    m = Motor(
        rotor=Rotor(math.pi / 2, Direction(0, 0, 1)),
        translator=Translator(Direction(1, 1, 0)),
    )
    assert isinstance(m.rotor, GeneralRotor)
    # v = ½(t_⊥ + cot(φ/2)·a×t_⊥); φ=π/2 → cot(π/4)=1, t_⊥=(1,1,0)
    assert m.rotor.origin.x == pytest.approx(0)
    assert m.rotor.origin.y == pytest.approx(1)
    assert m.rotor.origin.z == pytest.approx(0)
    assert m.translator.vector.x == pytest.approx(0)
    assert m.translator.vector.y == pytest.approx(0)
    assert m.translator.vector.z == pytest.approx(0)


def test_motor_decomposes_mixed():
    """Mixed translation → displaced axis + axial translation (screw)."""
    m = Motor(
        rotor=Rotor(math.pi / 2, Direction(0, 0, 1)),
        translator=Translator(Direction(1, 1, 1)),
    )
    assert isinstance(m.rotor, GeneralRotor)
    assert m.rotor.origin.x == pytest.approx(0)
    assert m.rotor.origin.y == pytest.approx(1)
    assert m.rotor.origin.z == pytest.approx(0)
    assert m.translator.vector.x == pytest.approx(0)
    assert m.translator.vector.y == pytest.approx(0)
    assert m.translator.vector.z == pytest.approx(1)


def test_motor_accepts_general_rotor():
    """A GeneralRotor + Translator input is stored verbatim (already screw form)."""
    gr = GeneralRotor(math.pi / 2, Direction(0, 0, 1), Point(0, 1, 0))
    m = Motor(gr, Translator(Direction(0, 0, 1)))
    assert m.rotor is gr
    assert m.translator.vector.z == pytest.approx(1)


def test_motor_screw_round_trip():
    """create(motor) → analyze returns the screw form and recreates the same MV."""
    b = BasisN3()
    mv = create_operator(
        b,
        Motor(
            rotor=Rotor(math.pi / 2, Direction(0, 0, 1)),
            translator=Translator(Direction(1, 1, 1)),
        ),
    )
    r = analyze_operator(mv)
    assert isinstance(r, Motor), f"Got {type(r).__name__}"
    assert r.rotor.angle == pytest.approx(math.pi / 2)
    assert r.rotor.origin.x == pytest.approx(0)
    assert r.rotor.origin.y == pytest.approx(1)
    assert r.rotor.origin.z == pytest.approx(0)
    assert r.translator.vector.x == pytest.approx(0)
    assert r.translator.vector.y == pytest.approx(0)
    assert r.translator.vector.z == pytest.approx(1)
    mv2 = create_operator(b, r)
    assert (mv2 - mv).mag < 1e-8
