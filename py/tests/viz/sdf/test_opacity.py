# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the SDF opacity transfer-function registry (Phase 12)."""

from __future__ import annotations

from pathlib import Path

from pytanga.viz.sdf.opacity import OpacityTransfer
from pytanga.viz.sdf.visualizer import SdfVisualizer

JS_REGISTRY = (
    Path(__file__).parents[3]
    / "pytanga"
    / "viz"
    / "templates"
    / "sdf"
    / "algebra"
    / "opacities.js"
)


def test_enum_values() -> None:
    # The enum value strings are the shared registry keys; the JS registry must
    # declare a matching key for each.
    js = JS_REGISTRY.read_text(encoding="utf-8")
    for member in OpacityTransfer:
        assert f"'{member.value}'" in js, f"{member.value} missing from JS registry"


def test_default_is_step() -> None:
    assert OpacityTransfer.default() is OpacityTransfer.STEP


def test_params_metadata() -> None:
    assert OpacityTransfer.STEP.params == ()
    assert OpacityTransfer.LINEAR.params == ("float epsilon",)
    assert OpacityTransfer.SIGMOID.params == ("float epsilon",)


def test_glsl_names() -> None:
    assert OpacityTransfer.STEP.glsl_name == "opacityOfStep"
    assert OpacityTransfer.LINEAR.glsl_name == "opacityOfLinear"
    assert OpacityTransfer.SIGMOID.glsl_name == "opacityOfSigmoid"


def test_snippet_purity() -> None:
    js = JS_REGISTRY.read_text(encoding="utf-8")
    assert "void main" not in js
    assert "opacityFuncs" in js
    # Each snippet is a standalone `opacityOf` function with no branching on
    # algebra/entity/opacity identity.
    assert js.count("float opacityOf(") == 3


def test_visualizer_opacity_setter_accepts_enum_and_str() -> None:
    viz = SdfVisualizer()
    assert viz.opacity == "step"  # default
    viz.opacity = "sigmoid"
    assert viz.opacity == "sigmoid"
    viz.opacity = OpacityTransfer.LINEAR
    assert viz.opacity == "linear"
