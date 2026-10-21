# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the ``ControlUI`` spec model + ``param_ui`` helper."""

from __future__ import annotations

from dataclasses import fields

from pytanga.viz import (
    CheckboxUI,
    ColorPickerUI,
    ControlUI,
    DropdownUI,
    SliderUI,
    TextFieldUI,
    ValueEditUI,
    infer_control_ui,
    param_ui,
)
from pytanga.viz._params_ui import _PARAM_UI_KEY, _ui_kwargs


def test_kinds_and_fields() -> None:
    assert SliderUI.kind == "slider"
    assert ValueEditUI.kind == "value_edit"
    assert DropdownUI.kind == "dropdown"
    assert CheckboxUI.kind == "checkbox"
    assert TextFieldUI.kind == "text"
    assert ColorPickerUI.kind == "color"
    assert [f.name for f in fields(SliderUI)] == [
        "title",
        "tooltip",
        "enabled",
        "skip",
        "min",
        "max",
        "step",
    ]


def test_param_ui_stores_under_reserved_key() -> None:
    f = param_ui(2.0, ui=SliderUI(min=0.1), units="m")
    assert f.default == 2.0
    assert f.metadata[_PARAM_UI_KEY] == SliderUI(min=0.1)
    assert f.metadata["units"] == "m"


def test_param_ui_without_ui() -> None:
    f = param_ui(2.0, doc="x")
    assert _PARAM_UI_KEY not in f.metadata
    assert f.metadata["doc"] == "x"


def test_infer_control_ui() -> None:
    assert isinstance(infer_control_ui(bool, True), CheckboxUI)
    assert infer_control_ui(int, 3) == ValueEditUI(step=1, digits=0)
    assert infer_control_ui(float, 2.0) == ValueEditUI()
    assert infer_control_ui(str, "x") == TextFieldUI()
    assert isinstance(infer_control_ui(str, "#4488ff"), ColorPickerUI)
    assert infer_control_ui(list, ["a", "b"]) == DropdownUI(options=["a", "b"])


def test_ui_kwargs_skips_shared_and_none() -> None:
    assert _ui_kwargs(SliderUI(title="T", min=0.1, max=5.0)) == {
        "min": 0.1,
        "max": 5.0,
    }
    assert _ui_kwargs(ControlUI(title="T")) == {}
