# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""The :class:`ParamsView` — a dict/dataclass rendered as label+control rows."""

from __future__ import annotations

import dataclasses
from typing import Any, cast

from ._base import View
from .._controls import ControlEvent, ControlHandler
from .._params_ui import ControlUI, _PARAM_UI_KEY, _ui_kwargs, infer_control_ui
from .control_views import (
    ButtonView,
    CheckboxView,
    ColorPickerView,
    DropdownView,
    LabelView,
    MarkdownView,
    ProgressBarView,
    SliderView,
    TextAreaView,
    TextFieldView,
    ValueEditView,
)


_VALUE_KINDS = frozenset(
    {"slider", "value_edit", "dropdown", "checkbox", "text", "textarea", "color"}
)

_KIND_TO_VIEW: dict[str, type[Any]] = {
    "slider": SliderView,
    "value_edit": ValueEditView,
    "dropdown": DropdownView,
    "checkbox": CheckboxView,
    "text": TextFieldView,
    "textarea": TextAreaView,
    "color": ColorPickerView,
    "button": ButtonView,
    "label": LabelView,
    "markdown": MarkdownView,
    "progress": ProgressBarView,
}


class ParamsView(View):
    """Render a mapping of values as key-label + control rows.

    Accepts a plain ``dict`` (with an optional ``styles`` dict of
    :class:`ControlUI` specs) or a ``@dataclass`` instance whose fields carry
    per-field UI metadata via :func:`param_ui` /
    ``field(metadata={"param_ui": …})``.  Every change fires ``on_change`` with
    the full state (the live ``dict`` or the mutated dataclass instance).
    """

    _node_type = "params_view"

    def __init__(
        self,
        source: dict[str, Any] | Any,
        styles: dict[str, ControlUI] | None = None,
        *,
        id: str | None = None,
        title: str = "",
        on_change: ControlHandler | None = None,
        **view_kwargs: Any,
    ) -> None:
        super().__init__(id=id, **view_kwargs)
        self.title = title
        self.on_change = on_change
        self.styles: dict[str, ControlUI] = dict(styles or {})
        self.instance: Any = None
        self._field_types: dict[str, Any] = {}
        self.values = self._initial_values(source)
        self._control_views: dict[str, Any] = {}
        self._titles: dict[str, str] = {}
        self._value_keys: set[str] = set()
        self.children: list[Any] = self._build_children()

    # ── construction ──────────────────────────────────────────

    def _initial_values(self, source: Any) -> dict[str, Any]:
        if isinstance(source, dict):
            return dict(source)
        if dataclasses.is_dataclass(source) and not isinstance(source, type):
            self.instance = source
            self._field_types = {
                f.name: f.type for f in dataclasses.fields(source)
            }
            return {
                f.name: getattr(source, f.name) for f in dataclasses.fields(source)
            }
        raise TypeError(
            "ParamsView source must be a dict or a dataclass instance, "
            f"got {type(source).__name__}"
        )

    def _resolve_ui(self, key: str) -> ControlUI | None:
        if key in self.styles:
            return self.styles[key]
        if self.instance is not None:
            field = next(
                (f for f in dataclasses.fields(self.instance) if f.name == key),
                None,
            )
            if field is not None and _PARAM_UI_KEY in field.metadata:
                return cast("ControlUI", field.metadata[_PARAM_UI_KEY])
        return None

    def _build_children(self) -> list[Any]:
        children: list[Any] = []
        for key, value in self.values.items():
            ui = self._resolve_ui(key)
            if ui is not None and ui.skip:
                continue
            if ui is None:
                py_type = self._field_types.get(key, type(value))
                ui = infer_control_ui(py_type, value)
            self._titles[key] = ui.title if ui.title else key
            if ui.kind in _VALUE_KINDS:
                self._value_keys.add(key)
            child = self._build_child(key, value, ui)
            self._control_views[key] = child
            children.append(child)
        return children

    def _build_child(self, key: str, value: Any, ui: ControlUI) -> Any:
        cid = f"{self.id}.{key}"
        kind = ui.kind
        kwargs = _ui_kwargs(ui)
        if ui.tooltip:
            kwargs["tooltip"] = ui.tooltip

        if kind in _VALUE_KINDS:
            if kind == "dropdown" and isinstance(value, (list, tuple)):
                value = value[0] if value else ""
            view = _KIND_TO_VIEW[kind](
                cid, label="", value=value, on_change=self._make_handler(key), **kwargs
            )
        elif kind == "button":
            view = ButtonView(
                cid, label="", on_click=self._make_click_handler(key), **kwargs
            )
        elif kind == "label":
            view = LabelView(cid, value=value, **kwargs)
        elif kind == "markdown":
            view = MarkdownView(cid, value=value, **kwargs)
        elif kind == "progress":
            view = ProgressBarView(cid, value=value, **kwargs)
        else:
            raise ValueError(f"unsupported control kind {kind!r}")

        view.control.hide_label = True
        if ui.enabled is not None:
            view.control.enabled = ui.enabled
        return view

    # ── handlers ──────────────────────────────────────────────

    def _make_handler(self, key: str) -> ControlHandler:
        async def _handler(value: Any, event: ControlEvent) -> None:
            self.values[key] = value
            if self.instance is not None:
                setattr(self.instance, key, value)
            if self.on_change is not None:
                await self.on_change(self._state(), event)

        return _handler

    def _make_click_handler(self, key: str) -> ControlHandler:
        async def _handler(value: Any, event: ControlEvent) -> None:
            if self.on_change is not None:
                await self.on_change(self._state(), event)

        return _handler

    def _state(self) -> Any:
        return self.instance if self.instance is not None else dict(self.values)

    # ── serialization ─────────────────────────────────────────

    def _serialize(self) -> dict[str, Any]:
        result = super()._serialize()
        result["title"] = self.title
        result["rows"] = [
            {
                "key": key,
                "title": self._titles[key],
                "control": self._control_views[key]._serialize(),
            }
            for key in self._control_views
        ]
        return result

    # ── runtime API ───────────────────────────────────────────

    def get_value(self) -> dict[str, Any]:
        """Return the current values as a plain ``dict``."""
        return dict(self.values)

    def set_value(self, key: str, value: Any) -> None:
        """Set one value (and push a ``control_update`` for value-bearing keys)."""
        self.values[key] = value
        if self.instance is not None:
            setattr(self.instance, key, value)
        view = self._control_views.get(key)
        if view is not None and key in self._value_keys:
            view.set_value(value)

    def set_values(self, mapping: dict[str, Any]) -> None:
        """Set several values at once (each pushes its own update)."""
        for key, value in mapping.items():
            self.set_value(key, value)

