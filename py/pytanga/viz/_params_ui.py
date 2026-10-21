# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Per-field control-UI metadata for :class:`~pytanga.viz.ParamsView`.

A :class:`ControlUI` (or one of its subclasses) describes how a single value is
rendered inside a :class:`ParamsView`: its control kind plus the kind-specific
parameters (``SliderUI.min``, ``DropdownUI.options``, …).  The value itself and
the ``on_change`` handler are deliberately **not** part of the spec — they come
from the field and the ``ParamsView`` respectively.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field, fields
from typing import Any, ClassVar, get_origin


@dataclass
class ControlUI:
    """Base UI spec shared by every control type."""

    title: str | None = None
    tooltip: str | None = None
    enabled: bool | None = None
    skip: bool = False
    kind: ClassVar[str] = ""


@dataclass
class SliderUI(ControlUI):
    """UI spec for a slider control."""

    kind: ClassVar[str] = "slider"
    min: float | None = None
    max: float | None = None
    step: float | None = None


@dataclass
class ValueEditUI(ControlUI):
    """UI spec for a numeric stepper control."""

    kind: ClassVar[str] = "value_edit"
    min: float | None = None
    max: float | None = None
    step: float | None = None
    digits: int | None = None
    editable: bool | None = None


@dataclass
class DropdownUI(ControlUI):
    """UI spec for a dropdown control."""

    kind: ClassVar[str] = "dropdown"
    options: list[str] | None = None


@dataclass
class CheckboxUI(ControlUI):
    """UI spec for a checkbox control."""

    kind: ClassVar[str] = "checkbox"


@dataclass
class TextFieldUI(ControlUI):
    """UI spec for a single-line text field."""

    kind: ClassVar[str] = "text"
    placeholder: str | None = None


@dataclass
class TextAreaUI(ControlUI):
    """UI spec for a multi-line text area."""

    kind: ClassVar[str] = "textarea"
    placeholder: str | None = None
    rows: int | None = None


@dataclass
class ColorPickerUI(ControlUI):
    """UI spec for a color picker."""

    kind: ClassVar[str] = "color"


@dataclass
class ButtonUI(ControlUI):
    """UI spec for a button (an action, not a value)."""

    kind: ClassVar[str] = "button"
    icon: str | None = None
    icon_only: bool = False


@dataclass
class LabelUI(ControlUI):
    """UI spec for a read-only label."""

    kind: ClassVar[str] = "label"
    font_size: float | None = None


@dataclass
class MarkdownUI(ControlUI):
    """UI spec for read-only rendered markdown."""

    kind: ClassVar[str] = "markdown"


@dataclass
class ProgressBarUI(ControlUI):
    """UI spec for a read-only progress bar."""

    kind: ClassVar[str] = "progress"
    total: float | None = None
    indeterminate: bool | None = None
    text: str | None = None


#: The reserved ``dataclasses.field(metadata=…)`` key that holds a
#: :class:`ControlUI` instance.  ``ParamsView`` reads only this key; every other
#: metadata key is user-owned and ignored.
_PARAM_UI_KEY = "param_ui"


def param_ui(
    default: Any,
    *,
    ui: ControlUI | None = None,
    **extra_metadata: Any,
) -> Any:
    """Return a ``dataclasses.field`` carrying control-UI metadata.

    ``ui`` is stored under the reserved ``metadata["param_ui"]`` key; every other
    keyword is passed through as additional (user-owned) metadata, so a field can
    carry ``param_ui`` alongside unrelated metadata without collision.
    """
    meta: dict[str, Any] = dict(extra_metadata)
    if ui is not None:
        meta[_PARAM_UI_KEY] = ui
    return field(default=default, metadata=meta)


#: Shared ``ControlUI`` fields that are not forwarded to the control constructor.
_SHARED_UI_FIELDS = frozenset({"title", "tooltip", "enabled", "skip"})

_COLOR_RE = re.compile(r"#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})")


def _looks_like_color(value: str) -> bool:
    """True for ``#rgb`` / ``#rrggbb`` hex strings."""
    return bool(_COLOR_RE.fullmatch(value))


def _is_sequence(py_type: Any, value: Any) -> bool:
    """True when *py_type*/*value* is a list or tuple (incl. parametrized)."""
    if isinstance(value, (list, tuple)):
        return True
    origin = get_origin(py_type)
    return origin in (list, tuple) or py_type in (list, tuple)


def infer_control_ui(py_type: Any, value: Any) -> ControlUI:
    """Infer a :class:`ControlUI` from a field/value type.

    Used by :class:`ParamsView` when a key has no explicit UI spec (no
    ``styles[key]`` and no ``"param_ui"`` field metadata).
    """
    if py_type is bool:
        return CheckboxUI()
    if py_type is int:
        return ValueEditUI(step=1, digits=0)
    if py_type is float:
        return ValueEditUI()
    if py_type is str or isinstance(value, str):
        if isinstance(value, str) and _looks_like_color(value):
            return ColorPickerUI()
        return TextFieldUI()
    if _is_sequence(py_type, value):
        options = [str(item) for item in value] if value else None
        return DropdownUI(options=options)
    return TextFieldUI()


def _ui_kwargs(ui: ControlUI) -> dict[str, Any]:
    """Return the subclass's non-``None``, kind-specific fields as constructor kwargs."""
    kwargs: dict[str, Any] = {}
    for f in fields(ui):
        if f.name in _SHARED_UI_FIELDS:
            continue
        val = getattr(ui, f.name)
        if val is not None:
            kwargs[f.name] = val
    return kwargs
