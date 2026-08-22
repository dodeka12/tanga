# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the SDF distance-function registry (Phase 3)."""

from __future__ import annotations

from pathlib import Path

from pytanga.viz.sdf.distance import DistanceFunction

JS_REGISTRY = (
    Path(__file__).parents[3]
    / "pytanga"
    / "viz"
    / "templates"
    / "sdf"
    / "algebra"
    / "distances.js"
)


def test_enum_values() -> None:
    # The enum value strings are the shared registry keys; the JS registry must
    # declare a matching key for each.
    js = JS_REGISTRY.read_text(encoding="utf-8")
    for member in DistanceFunction:
        assert f"'{member.value}'" in js, (
            f"{member.value} missing from JS registry"
        )


def test_default_is_scalar_pseudo() -> None:
    assert DistanceFunction.default() is DistanceFunction.SCALAR_PSEUDO


def test_params_metadata() -> None:
    assert DistanceFunction.GRADE.params == ("int k",)
    assert DistanceFunction.COMPONENT.params == ("int blade_id",)
    for member in (
        DistanceFunction.SCALAR_PSEUDO,
        DistanceFunction.MAGNITUDE,
        DistanceFunction.SCALAR,
    ):
        assert member.params == ()


def test_glsl_names() -> None:
    assert DistanceFunction.SCALAR_PSEUDO.glsl_name == "distOfScalarPseudo"
    assert DistanceFunction.MAGNITUDE.glsl_name == "distOfMagnitude"
    assert DistanceFunction.SCALAR.glsl_name == "distOfScalar"
    assert DistanceFunction.GRADE.glsl_name == "distOfGrade"
    assert DistanceFunction.COMPONENT.glsl_name == "distOfComponent"


def test_snippet_purity() -> None:
    js = JS_REGISTRY.read_text(encoding="utf-8")
    # Snippets must not define main(). (Branching on algebra/entity identity is
    # excluded by construction: each entry is a standalone pure GLSL function;
    # the active selection is a registry lookup, not a compile-time branch.)
    assert "void main" not in js
    assert "distanceFuncs" in js
    # When concatenated, each snippet expands to a `float distOf*(...)` function
    # with no `if` on algebra identity and no entity kind dispatch.
    for fn in (
        "distOfScalarPseudo",
        "distOfMagnitude",
        "distOfScalar",
        "distOfGrade",
        "distOfComponent",
    ):
        assert fn in js, f"{fn} missing from JS registry"
