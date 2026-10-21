# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the ``ControlUI`` spec model + ``param_ui`` helper."""

from __future__ import annotations

from dataclasses import fields
from enum import Enum
from typing import Literal, Optional

from pytanga.viz import (
    ButtonUI,
    CheckboxUI,
    ColorPickerUI,
    ControlUI,
    DropdownUI,
    MarkdownUI,
    ProgressBarUI,
    SliderUI,
    TextFieldUI,
    ValueEditUI,
    infer_control_ui,
    param_ui,
)
from pytanga.viz._params_ui import _PARAM_UI_KEY, _ui_kwargs, coerce_value


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
        "visible",
        "skip",
        "on_change",
        "coerce",
        "validate",
        "full_width",
        "min",
        "max",
        "step",
        "integer",
    ]


def test_full_width_defaults() -> None:
    assert ButtonUI().full_width is True
    assert MarkdownUI().full_width is True
    assert ProgressBarUI().full_width is True
    assert SliderUI().full_width is False


def test_button_label() -> None:
    assert ButtonUI(label="Compute circles").label == "Compute circles"


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


class _Mode(Enum):
    SOLID = "solid"
    WIRE = "wire"


def test_infer_enum_literal_optional() -> None:
    assert infer_control_ui(_Mode, _Mode.SOLID) == DropdownUI(
        options=["solid", "wire"]
    )
    assert infer_control_ui(Literal["a", "b"], "a") == DropdownUI(options=["a", "b"])
    assert infer_control_ui(Optional[int], 3) == ValueEditUI(step=1, digits=0)
    assert infer_control_ui(int | None, 3) == ValueEditUI(step=1, digits=0)


def test_coerce_value() -> None:
    assert coerce_value(int, 3.0) == 3
    assert coerce_value(float, 3) == 3.0
    assert coerce_value(bool, 1) is True
    assert coerce_value(str, 3) == "3"
    assert coerce_value(_Mode, "solid") is _Mode.SOLID
    assert coerce_value(Optional[int], 2.5) == 2
    assert coerce_value(int, None) is None
