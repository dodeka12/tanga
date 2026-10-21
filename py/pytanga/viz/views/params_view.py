# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""The :class:`ParamsView` — a dict/dataclass rendered as label+control rows."""

from __future__ import annotations

import dataclasses
import logging
import typing
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Literal, cast

from ._base import View
from .._controls import ControlEvent, ControlHandler
from .._params_ui import (
    ControlUI,
    GroupUI,
    _PARAM_UI_KEY,
    _ui_kwargs,
    coerce_value,
    infer_control_ui,
)
from .group_view import GroupView
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

_DISPLAY_KINDS = frozenset({"label", "markdown", "progress"})

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


def _resolve_field_types(instance: Any) -> dict[str, Any]:
    """Resolve a dataclass's real field types (handles string annotations).

    ``from __future__ import annotations`` turns every annotation into a string,
    so ``dataclasses.fields(...).type`` is unusable; ``typing.get_type_hints``
    resolves them (and ``Optional``/``X | None``) back to concrete types.
    """
    try:
        hints = typing.get_type_hints(type(instance), include_extras=True)
    except Exception:
        return {f.name: f.type for f in dataclasses.fields(instance)}
    return {f.name: hints.get(f.name, f.type) for f in dataclasses.fields(instance)}


def _title_from_key(key: str) -> str:
    """Derive a row title from a snake_case key (``radius_mm`` → "Radius mm")."""
    return key.replace("_", " ").strip().capitalize()


@dataclass
class RowSpec:
    """A non-parameter row rendered inside a :class:`ParamsView`.

    ``ui`` is the row's :class:`ControlUI` spec (a button, label, markdown,
    progress bar, …), ``value`` its initial value, and ``on_click`` / ``on_change``
    the row's handler (falling back to the ``ParamsView``'s shared ``on_change``
    when unset).  ``position`` places the row above or below the parameter rows.
    """

    key: str
    ui: ControlUI
    value: Any = None
    on_click: ControlHandler | None = None
    on_change: ControlHandler | None = None
    position: Literal["above", "below"] = "below"


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
        extra_rows: list[RowSpec] | None = None,
        title_from_name: bool = False,
        dense: bool = False,
        **view_kwargs: Any,
    ) -> None:
        super().__init__(id=id, **view_kwargs)
        self.title = title
        self.on_change = on_change
        self.styles: dict[str, ControlUI] = dict(styles or {})
        self.extra_rows: list[RowSpec] = list(extra_rows or [])
        self.title_from_name = title_from_name
        self.dense = dense
        self.instance: Any = None
        self._field_types: dict[str, Any] = {}
        self.values = self._initial_values(source)
        self._control_views: dict[str, Any] = {}
        self._titles: dict[str, str] = {}
        self._value_keys: set[str] = set()
        self._display_keys: set[str] = set()
        self._row_keys: list[str] = []
        self._push_state = None  # callback slot injected at mount
        self._push_layout = None  # callback slot injected at mount (structural changes)
        self.children: list[Any] = self._build_children()

    # ── construction ──────────────────────────────────────────

    def _initial_values(self, source: Any) -> dict[str, Any]:
        if isinstance(source, dict):
            return dict(source)
        if dataclasses.is_dataclass(source) and not isinstance(source, type):
            self.instance = source
            self._field_types = _resolve_field_types(source)
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

    def _field_meta(self, key: str) -> dict[str, Any]:
        """Return the dataclass field's ``metadata`` dict (empty for dict mode)."""
        if self.instance is None:
            return {}
        field = next(
            (f for f in dataclasses.fields(self.instance) if f.name == key), None
        )
        return dict(field.metadata) if field is not None else {}

    def _tooltip_for(self, key: str, ui: ControlUI) -> str | None:
        """Resolve a row's tooltip: ``ui.tooltip``, else ``metadata["description"]``."""
        if ui.tooltip:
            return ui.tooltip
        description = self._field_meta(key).get("description")
        return description if isinstance(description, str) else None

    def _title_for(self, key: str, ui: ControlUI) -> str:
        """Resolve a row's title: ``ui.title``, else a ``title_from_name`` transform."""
        if ui.title:
            return ui.title
        if self.title_from_name:
            return _title_from_key(key)
        return key

    def _build_children(self) -> list[Any]:
        children: list[Any] = []
        above = [r for r in self.extra_rows if r.position == "above"]
        below = [r for r in self.extra_rows if r.position == "below"]

        for spec in above:
            self._append_row(children, spec)

        for key, value in self.values.items():
            ui = self._resolve_ui(key)
            if ui is not None and ui.skip:
                continue
            if ui is None and self._is_group_value(value):
                ui = GroupUI()
            if isinstance(ui, GroupUI):
                self._titles[key] = ""
                child = self._build_group(key, value, ui)
            else:
                if ui is None:
                    py_type = self._field_types.get(key, type(value))
                    ui = infer_control_ui(py_type, value)
                self._titles[key] = self._title_for(key, ui)
                if ui.kind in _VALUE_KINDS:
                    self._value_keys.add(key)
                elif ui.kind in _DISPLAY_KINDS:
                    self._display_keys.add(key)
                child = self._build_child(key, value, ui, ui.on_change, ui.on_change)
            self._control_views[key] = child
            self._row_keys.append(key)
            children.append(child)

        for spec in below:
            self._append_row(children, spec)

        return children

    def _is_group_value(self, value: Any) -> bool:
        """True when *value* is a dataclass instance (→ a nested group)."""
        return bool(dataclasses.is_dataclass(value) and not isinstance(value, type))

    def _build_group(self, key: str, value: Any, ui: GroupUI) -> GroupView:
        """Build a nested ``GroupView`` wrapping a nested ``ParamsView``."""
        title = ui.title if ui.title else key
        nested = ParamsView(value, id=f"{self.id}.{key}")
        return GroupView(title=title, children=[nested], collapsed=ui.collapsed)

    def _append_row(self, children: list[Any], spec: RowSpec) -> None:
        """Build and append a single non-parameter row (above/below the params)."""
        key = spec.key
        ui = spec.ui
        self._titles[key] = self._title_for(key, ui)
        if ui.kind in _VALUE_KINDS:
            self._value_keys.add(key)
        elif ui.kind in _DISPLAY_KINDS:
            self._display_keys.add(key)
        child = self._build_child(key, spec.value, ui, spec.on_change, spec.on_click)
        self._control_views[key] = child
        self._row_keys.append(key)
        children.append(child)

    def _build_child(
        self,
        key: str,
        value: Any,
        ui: ControlUI,
        field_handler: ControlHandler | None = None,
        click_handler: ControlHandler | None = None,
    ) -> Any:
        cid = f"{self.id}.{key}"
        kind = ui.kind
        kwargs = _ui_kwargs(ui)
        tooltip = self._tooltip_for(key, ui)
        if tooltip:
            kwargs["tooltip"] = tooltip

        if kind in _VALUE_KINDS:
            if kind == "dropdown":
                if isinstance(value, (list, tuple)):
                    value = value[0] if value else ""
                elif isinstance(value, Enum):
                    value = value.value
            view = _KIND_TO_VIEW[kind](
                cid,
                label="",
                value=value,
                on_change=self._make_handler(
                    key, field_handler, self._coerce_for(key, ui), getattr(ui, "validate", None)
                ),
                **kwargs,
            )
        elif kind == "button":
            view = ButtonView(
                cid, label="", on_click=self._make_click_handler(key, click_handler), **kwargs
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
        if ui.visible is not None:
            view.control.visible = ui.visible
        return view

    # ── handlers ──────────────────────────────────────────────

    def _coerce_for(self, key: str, ui: ControlUI) -> Callable[[Any], Any] | None:
        """Return the coercion to apply to *key*'s incoming values (or ``None``)."""
        if ui.coerce is not None:
            return ui.coerce
        if getattr(ui, "integer", False):
            return int
        py_type = self._field_types.get(key)
        if py_type is None:
            return None

        def _coerce(value: Any) -> Any:
            return coerce_value(py_type, value)

        return _coerce

    def _make_handler(
        self,
        key: str,
        field_handler: ControlHandler | None = None,
        coerce: Callable[[Any], Any] | None = None,
        validate: Callable[[Any], bool | str] | None = None,
    ) -> ControlHandler:
        async def _handler(value: Any, event: ControlEvent) -> None:
            if coerce is not None:
                value = coerce(value)
            if validate is not None:
                verdict = validate(value)
                if verdict is not True:
                    if isinstance(verdict, str):
                        logging.getLogger(__name__).warning(
                            "ParamsView rejected %r: %s", key, verdict
                        )
                    view = self._control_views.get(key)
                    if view is not None:
                        view.set_value(self.values.get(key))
                    return
            event.key = key
            event.value = value
            self.values[key] = value
            if self.instance is not None and key in self._field_types:
                setattr(self.instance, key, value)
            if field_handler is not None:
                await field_handler(value, event)
            elif self.on_change is not None:
                await self.on_change(self._state(), event)

        return _handler

    def _make_click_handler(
        self, key: str, field_handler: ControlHandler | None = None
    ) -> ControlHandler:
        async def _handler(value: Any, event: ControlEvent) -> None:
            event.key = key
            event.value = value
            if field_handler is not None:
                await field_handler(value, event)
            elif self.on_change is not None:
                await self.on_change(self._state(), event)

        return _handler

    def _state(self) -> Any:
        return self.instance if self.instance is not None else dict(self.values)

    # ── serialization ─────────────────────────────────────────

    def _serialize(self) -> dict[str, Any]:
        result = super()._serialize()
        result["title"] = self.title
        if self.dense:
            result["dense"] = True
        result["rows"] = [
            {
                "key": key,
                "title": self._titles[key],
                "control": self._control_views[key]._serialize(),
            }
            for key in self._row_keys
        ]
        return result

    # ── runtime API ───────────────────────────────────────────

    def get_value(self) -> dict[str, Any]:
        """Return the current values as a plain ``dict``."""
        return dict(self.values)

    def set_value(self, key: str, value: Any) -> None:
        """Set one value and push an update for value-bearing/display rows.

        Does not fire ``on_change``.  Rows that are not dataclass fields (e.g.
        ``extra_rows`` display rows) are updated in place without being added to
        ``get_value()``.
        """
        view = self._control_views.get(key)
        if view is None:
            return
        is_param = key in self._field_types or key in self.values
        if is_param:
            self.values[key] = value
            if self.instance is not None and key in self._field_types:
                setattr(self.instance, key, value)
        if key in self._value_keys or key in self._display_keys:
            view.set_value(value)

    def set_values(self, mapping: dict[str, Any]) -> None:
        """Set several values at once (each pushes its own update)."""
        for key, value in mapping.items():
            self.set_value(key, value)

    def set_visible(self, key: str, visible: bool) -> None:
        """Show/hide a whole row (title + control)."""
        view = self._control_views.get(key)
        if view is not None:
            view.set_visible(visible)

    def set_enabled(self, key: str, enabled: bool) -> None:
        """Enable/disable a whole row (title + control)."""
        view = self._control_views.get(key)
        if view is not None:
            view.set_enabled(enabled)

    def set_title(self, key: str, title: str) -> None:
        """Rename a row's key label at runtime."""
        if key not in self._titles:
            raise KeyError(f"unknown row {key!r}")
        self._titles[key] = title
        if self._push_state is not None:
            self._push_state(self.id, {"row": key, "title": title})

    def set_options(self, key: str, options: Any) -> None:
        """Replace a dropdown row's options at runtime."""
        view = self._control_views.get(key)
        if view is not None and isinstance(view, DropdownView):
            view.set_options(options)

    def set_state(self, new_instance_or_dict: Any) -> None:
        """Replace the whole state without firing ``on_change``.

        Re-binds the source (a ``dict`` or dataclass instance), re-derives the
        field types, and pushes the new value for every still-existing value row.
        Use :meth:`add` / :meth:`remove` for structural (shape) changes.
        """
        if isinstance(new_instance_or_dict, dict):
            self.instance = None
            self._field_types = {}
            new_values = dict(new_instance_or_dict)
        elif dataclasses.is_dataclass(new_instance_or_dict) and not isinstance(
            new_instance_or_dict, type
        ):
            self.instance = new_instance_or_dict
            self._field_types = _resolve_field_types(new_instance_or_dict)
            new_values = {
                f.name: getattr(new_instance_or_dict, f.name)
                for f in dataclasses.fields(new_instance_or_dict)
            }
        else:
            raise TypeError(
                "set_state expects a dict or dataclass instance, "
                f"got {type(new_instance_or_dict).__name__}"
            )
        self.values = new_values
        for key in self._row_keys:
            view = self._control_views.get(key)
            if view is not None and key in self._value_keys and key in self.values:
                view.set_value(self.values[key])

    def add(self, key: str, value: Any, ui: ControlUI) -> None:
        """Add a row at runtime and re-push the layout."""
        if key in self._control_views:
            raise ValueError(f"row {key!r} already exists")
        self._titles[key] = ui.title if ui.title else key
        if ui.kind in _VALUE_KINDS:
            self._value_keys.add(key)
            self.values[key] = value
        elif ui.kind in _DISPLAY_KINDS:
            self._display_keys.add(key)
        child = self._build_child(key, value, ui, ui.on_change, ui.on_change)
        self._control_views[key] = child
        self._row_keys.append(key)
        self.children.append(child)
        if self._push_layout is not None:
            self._push_layout()

    def remove(self, key: str) -> None:
        """Remove a row at runtime and re-push the layout."""
        view = self._control_views.pop(key, None)
        if view is None:
            return
        self._titles.pop(key, None)
        self._value_keys.discard(key)
        self._display_keys.discard(key)
        if key in self._row_keys:
            self._row_keys.remove(key)
        if view in self.children:
            self.children.remove(view)
        self.values.pop(key, None)
        if self._push_layout is not None:
            self._push_layout()

