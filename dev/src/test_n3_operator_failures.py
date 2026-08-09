#!/usr/bin/env python3
"""Demonstrate N3 operator analysis failures.

Run: uv run python dev/src/test_n3_operator_failures.py
"""

from __future__ import annotations

import math

from pytanga.basis import BasisN3
from pytanga.geometry import Geometry
from pytanga.geometry.analysis import analyze_operator
from pytanga.geometry.create import create_operator
from pytanga.geometry.entities import Direction, Point
from pytanga.geometry.operators import (
    GeneralRotor,
    Motor,
    Rotor,
    Translator,
)

b = BasisN3()
geo = Geometry(b)

# --- Rotor ---
print("=== Rotor ===")
mv = create_operator(b, Rotor(math.pi / 2, Direction(0, 0, 1)))
mv.show("rotor")
r = analyze_operator(mv)
print("Created: Rotor(π/2, z)")
print(f"Analyzed: {r}")
print("\n")

p = geo.create(Point(1, 2, 3))
p.show("p")
q = mv * p * ~mv
q.show("q")
print(geo.which_entity(q))

trans = geo.create(Translator(Direction(0, 0, 1)))
trans.show("trans")
q = trans * p * ~trans
q.show("trans(p)")
print(geo.which_entity(q))

# --- Motor ---
print("=== Motor ===")
mv = create_operator(
    b,
    Motor(
        rotor=Rotor(math.pi / 2, Direction(0, 0, 1)),
        translator=Translator(Direction(0, 0, 1)),
    ),
)
r = analyze_operator(mv)
print("Created: Motor(R(90°z), T(0,0,1))")
print(f"Analyzed: {r}")
print(f"  rotor.angle = {r.rotor.angle}")
print(f"  rotor.axis  = {r.rotor.axis}")
print(f"  translator  = {r.translator}")
print("\n")

# --- GeneralRotor ---
print("=== GeneralRotor ===")
mv = create_operator(b, GeneralRotor(math.pi / 2, Direction(0, 0, 1), Point(1, 0, 0)))
r = analyze_operator(mv)
print("Created: GeneralRotor(π/2, z, origin=(1,0,0))")
print(f"Analyzed: {r}")
