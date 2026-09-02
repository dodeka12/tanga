# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Declarative view/layout model for the Tanga 3D viewer.

A :class:`View` is a rectangular region with per-axis preferred and min/max
sizes.  Leaves (:class:`SceneView`, :class:`SpacerView`, and the HTML control
views :class:`SliderView`/:class:`ButtonView`/:class:`DropdownView`) and two
containers (:class:`SplitView` with draggable splitters and :class:`StackView`
flow layout) are provided, plus :class:`GroupView` (a titled stack, usable as an
overlay).  The whole tree serializes to the ``view_layout`` message consumed by
the browser frontend.

This module is pure data + validation: it imports nothing from the rendering or
server layers, so it is unit-testable in isolation.
"""

from __future__ import annotations

from itertools import count
from typing import Any, Iterator, Literal

from ._controls import (
    Button,
    Checkbox,
    ColorPicker,
    Control,
    Dropdown,
    EControlVariant,
    FileChooser,
    Handler,
    Slider,
    Table,
    TextArea,
    TextField,
    ValueEdit,
    _serialize_one_control,
)
from ._anchor import EAnchor
from ._icons import Icon
from ._size import Size, SizeSpec, size_from_dict
from .camera import CameraConfig, View2DConfig, View3dConfig, _normalize_camera_config

Orientation = Literal["horizontal", "vertical"]
StackDirection = Literal["vertical", "horizontal", "wrap"]

#: Default minimum extent for a scene pane on both axes, so a scene can never
#: be collapsed to nothing (override per view, or pass ``None`` to disable).
_DEFAULT_SCENE_MIN = Size.px(120)


def _size_dict(spec: SizeSpec) -> dict | None:
    """Serialize a ``SizeSpec`` to the canonical JSON shape (``None`` → ``null``)."""
    return None if spec is None else spec.to_dict()


def _coerce_scene_name(scene: Any) -> str:
    """Accept a scene name string or an object exposing ``.name`` (handle/scene)."""
    if isinstance(scene, str):
        return scene
    name = getattr(scene, "name", None)
    if isinstance(name, str):
        return name
    raise TypeError(f"Expected a scene name or handle, got {type(scene).__name__}")


def _make_id_gen() -> Iterator[str]:
    """Yield stable, deterministic node ids in DFS order."""
    counter = count()
    while True:
        yield f"v{next(counter)}"


#: Process-wide counter for auto-generated ``SceneView`` pane ids (``sv0``…).
#: A scene pane needs a stable id so it can be targeted at runtime
#: (``Visualizer.set_view_camera``) after the layout has been serialized.
_scene_view_counter = count()


class View:
    """Base for every pane/container in a layout. Split-agnostic.

    Exposes per-axis preferred/min/max sizes.  ``fixed_x``/``fixed_y`` are
    computed (``min == max``) and are what a container uses to decide whether a
    splitter next to this view is draggable.
    """

    _node_type = "view"

    def __init__(
        self,
        *,
        size: SizeSpec = None,
        preferred_width: SizeSpec = None,
        preferred_height: SizeSpec = None,
        min_width: SizeSpec = None,
        min_height: SizeSpec = None,
        max_width: SizeSpec = None,
        max_height: SizeSpec = None,
    ) -> None:
        if size is not None:
            if preferred_width is None:
                preferred_width = size
            if preferred_height is None:
                preferred_height = size
        self.preferred_width = preferred_width
        self.preferred_height = preferred_height
        self.min_width = min_width
        self.min_height = min_height
        self.max_width = max_width
        self.max_height = max_height

    @property
    def fixed_x(self) -> bool:
        """True when the width is pinned (``min_width == max_width``)."""
        return (
            self.min_width is not None
            and self.max_width is not None
            and self.min_width == self.max_width
        )

    @property
    def fixed_y(self) -> bool:
        """True when the height is pinned (``min_height == max_height``)."""
        return (
            self.min_height is not None
            and self.max_height is not None
            and self.min_height == self.max_height
        )

    def _serialize(self, id_gen: Iterator[str]) -> dict[str, Any]:
        """Serialize this node (subclasses append their type-specific fields)."""
        return {
            "type": self._node_type,
            "id": next(id_gen),
            "min_width": _size_dict(self.min_width),
            "max_width": _size_dict(self.max_width),
            "min_height": _size_dict(self.min_height),
            "max_height": _size_dict(self.max_height),
            "preferred_width": _size_dict(self.preferred_width),
            "preferred_height": _size_dict(self.preferred_height),
        }


class SceneView(View):
    """A pane that renders a named scene (referenced by name or handle).

    Scene panes default to a small minimum size on both axes (``min_width`` and
    ``min_height``) so a splitter cannot collapse them to nothing.  Pass
    explicit ``min_width``/``min_height`` (``None`` disables the floor).

    ``camera`` overrides the scene's own camera for **this pane only**, so the
    same scene can be shown from different viewpoints in separate panes.  It
    accepts a :class:`~pytanga.viz.camera.CameraConfig` (or a
    :class:`~pytanga.viz.camera.View2DConfig` /
    :class:`~pytanga.viz.camera.View3dConfig`, which is converted); pass
    ``None`` (default) to use the scene's camera.

    ``id`` is an optional stable identifier for the pane (auto-generated as
    ``"svN"`` when omitted).  It is the key used to address this pane at runtime
    (e.g. ``Visualizer.set_view_camera``).

    ``overlay`` lists views that float over the canvas (e.g. a ``GroupView``),
    anchored by each child's ``position``.
    """

    _node_type = "scene_view"

    def __init__(
        self,
        scene: Any,
        *,
        id: str | None = None,
        camera: CameraConfig | View2DConfig | View3dConfig | None = None,
        overlay: list[View] | None = None,
        **kwargs: Any,
    ) -> None:
        kwargs.setdefault("min_width", _DEFAULT_SCENE_MIN)
        kwargs.setdefault("min_height", _DEFAULT_SCENE_MIN)
        super().__init__(**kwargs)
        self.scene = _coerce_scene_name(scene)
        self.id = id if id is not None else f"sv{next(_scene_view_counter)}"
        self.camera = _normalize_camera_config(camera)
        self.overlay = list(overlay or [])

    def _serialize(self, id_gen: Iterator[str]) -> dict[str, Any]:
        result = super()._serialize(id_gen)
        result["id"] = self.id
        result["scene"] = self.scene
        if self.camera is not None:
            result["camera"] = self.camera.to_dict()
        if self.overlay:
            result["children"] = [child._serialize(id_gen) for child in self.overlay]
        return result


class SpacerView(View):
    """An empty, fully-flexible filler pane."""

    _node_type = "spacer"


class SplitView(View):
    """A container that lays its children out along one axis."""

    _node_type = "split"

    def __init__(
        self,
        orientation: Orientation,
        children: list[View] | None = None,
        *,
        movable: bool | None = None,
        sizes: list[SizeSpec] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        if orientation not in ("horizontal", "vertical"):
            raise ValueError(
                f"orientation must be 'horizontal' or 'vertical', got {orientation!r}"
            )
        self.orientation = orientation
        self.children = list(children or [])
        self.movable = movable
        self.sizes = sizes
        if len(self.children) < 2:
            raise ValueError("SplitView requires at least 2 children")
        if self.sizes is not None and len(self.sizes) != len(self.children):
            raise ValueError(
                f"sizes must match children ({len(self.sizes)} != {len(self.children)})"
            )

    def _serialize(self, id_gen: Iterator[str]) -> dict[str, Any]:
        result = super()._serialize(id_gen)
        result["orientation"] = self.orientation
        result["movable"] = self.movable
        result["sizes"] = (
            [_size_dict(s) for s in self.sizes]
            if self.sizes is not None
            else [None] * len(self.children)
        )
        result["children"] = [child._serialize(id_gen) for child in self.children]
        return result


class StackView(View):
    """A flow container that stacks children vertically, horizontally, or wraps.

    Unlike :class:`SplitView`, children flow in normal document order (no
    splitters) and the container sizes to its content along the stack axis.
    """

    _node_type = "stack"

    def __init__(
        self,
        direction: StackDirection,
        children: list[View] | None = None,
        *,
        scrollable: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        if direction not in ("vertical", "horizontal", "wrap"):
            raise ValueError(
                f"direction must be 'vertical', 'horizontal' or 'wrap', got {direction!r}"
            )
        self.direction = direction
        self.children = list(children or [])
        self.scrollable = scrollable

    def _serialize(self, id_gen: Iterator[str]) -> dict[str, Any]:
        result = super()._serialize(id_gen)
        result["direction"] = self.direction
        result["scrollable"] = self.scrollable
        result["children"] = [child._serialize(id_gen) for child in self.children]
        return result


class GroupView(StackView):
    """A titled view container (a :class:`StackView` with panel chrome).

    Holds control views (or any views) and can be used as a split pane or as an
    overlay child of a :class:`SceneView`, where ``position`` anchors it over the
    canvas.
    """

    _node_type = "group"

    def __init__(
        self,
        title: str = "",
        children: list[View] | None = None,
        *,
        direction: StackDirection = "vertical",
        position: EAnchor | None = None,
        collapsed: bool = False,
        scrollable: bool = False,
        icon: Icon | None = None,
        icon_only: bool = False,
        parent_id: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(direction, children, scrollable=scrollable, **kwargs)
        self.title = title
        self.position = position
        self.collapsed = collapsed
        self.icon = icon
        self.icon_only = icon_only
        self.parent_id = parent_id

    def _serialize(self, id_gen: Iterator[str]) -> dict[str, Any]:
        result = super()._serialize(id_gen)
        result["title"] = self.title
        result["position"] = self.position
        result["collapsed"] = self.collapsed
        if self.icon is not None:
            result["icon"] = str(self.icon)
        result["icon_only"] = self.icon_only
        if self.parent_id is not None:
            result["parent_id"] = self.parent_id
        return result


def _apply_menu_variant(view: View) -> None:
    """Recursively force ``MENU`` onto eligible control views in a menu subtree."""
    for child in getattr(view, "children", None) or ():
        if isinstance(child, MenuView):
            if child.override_variant:
                _apply_menu_variant(child)
            continue
        ctrl = getattr(child, "control", None)
        if ctrl is not None and hasattr(ctrl, "variant"):
            ctrl.variant = EControlVariant.MENU
        _apply_menu_variant(child)


class MenuView(View):
    """A menu: a hamburger dropdown or a permanent horizontal strip of options.

    ``children`` are the options (usually ``*View`` control wrappers); a child
    may itself be another :class:`MenuView`, forming a nested sub-menu.  When
    used as an overlay (the global overlay or a :class:`SceneView` overlay
    child), ``position`` anchors the menu.

    ``override_variant`` (default ``True``) forces every eligible control in the
    subtree to the ``MENU`` variant, so options render flat/borderless without
    setting ``variant=`` by hand.
    """

    _node_type = "menu"

    def __init__(
        self,
        label: str = "",
        children: list[View] | None = None,
        *,
        trigger_icon: Icon | None = None,
        mode: Literal["dropdown", "bar"] = "dropdown",
        direction: StackDirection | None = None,
        position: EAnchor | None = None,
        override_variant: bool = True,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        if mode not in ("dropdown", "bar"):
            raise ValueError(f"mode must be 'dropdown' or 'bar', got {mode!r}")
        if direction is None:
            direction = "horizontal" if mode == "bar" else "vertical"
        if direction not in ("vertical", "horizontal", "wrap"):
            raise ValueError(
                f"direction must be 'vertical', 'horizontal' or 'wrap', got {direction!r}"
            )
        self.label = label
        self.trigger_icon = trigger_icon
        self.mode = mode
        self.direction = direction
        self.position = position
        self.override_variant = override_variant
        self.children = list(children or [])
        if override_variant:
            _apply_menu_variant(self)

    def _serialize(self, id_gen: Iterator[str]) -> dict[str, Any]:
        result = super()._serialize(id_gen)
        result["trigger_icon"] = (
            str(self.trigger_icon) if self.trigger_icon is not None else None
        )
        result["label"] = self.label
        result["mode"] = self.mode
        result["direction"] = self.direction
        result["position"] = self.position
        result["children"] = [child._serialize(id_gen) for child in self.children]
        return result


class ControlView(View):
    """Base for a single HTML control rendered as a plain ``View`` (no scene).

    The control ``id`` is the WebSocket event key (``control_id``) and must be
    unique across the app.  Each subclass wraps a
    :class:`~pytanga.viz._controls.Control` (``self.control``) which is the
    single source of truth for the control's fields; reads of those fields
    delegate to it via :meth:`__getattr__`.
    """

    _node_type = "control"

    def __init__(
        self,
        cid: str,
        *,
        label: str = "",
        tooltip: str = "",
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.id = cid
        self.label = label
        self.tooltip = tooltip
        self.control: Control | None = None

    def __getattr__(self, name: str) -> Any:
        ctrl = self.__dict__.get("control")
        if ctrl is not None and hasattr(ctrl, name):
            return getattr(ctrl, name)
        raise AttributeError(f"{type(self).__name__} object has no attribute {name!r}")

    def _serialize(self, id_gen: Iterator[str]) -> dict[str, Any]:
        result = super()._serialize(id_gen)
        result["id"] = self.id  # control id doubles as the event key
        result["label"] = self.label
        result["tooltip"] = self.tooltip
        for key, val in _serialize_one_control(self.control).items():
            if key not in ("id", "kind", "label", "tooltip"):
                result[key] = val
        return result


class SliderView(ControlView):
    """A numeric slider control as a view."""

    _node_type = "slider_view"

    def __init__(
        self,
        cid: str,
        *,
        label: str = "",
        variant: EControlVariant = EControlVariant.DEFAULT,
        min: float = 0.0,
        max: float = 1.0,
        step: float = 0.01,
        value: float | None = None,
        on_change: Handler | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(cid, label=label, **kwargs)
        self.control = Slider(
            id=cid,
            label=label,
            tooltip=self.tooltip,
            variant=variant,
            min=float(min),
            max=float(max),
            step=float(step),
            value=float(min) if value is None else float(value),
            on_change=on_change,
        )


class ButtonView(ControlView):
    """A clickable button control (with optional icon) as a view."""

    _node_type = "button_view"

    def __init__(
        self,
        cid: str,
        *,
        label: str = "",
        variant: EControlVariant = EControlVariant.DEFAULT,
        icon: Icon | None = None,
        icon_only: bool = False,
        on_click: Handler | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(cid, label=label, **kwargs)
        self.control = Button(
            id=cid,
            label=label,
            tooltip=self.tooltip,
            variant=variant,
            icon=icon,
            icon_only=icon_only,
            on_click=on_click,
        )


class DropdownView(ControlView):
    """A dropdown/select control as a view."""

    _node_type = "dropdown_view"

    def __init__(
        self,
        cid: str,
        *,
        label: str = "",
        options: list[str] | tuple[str, ...] = (),
        value: str = "",
        on_change: Handler | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(cid, label=label, **kwargs)
        self.control = Dropdown(
            id=cid,
            label=label,
            tooltip=self.tooltip,
            options=list(options),
            value=value,
            on_change=on_change,
        )


class FileChooserView(ControlView):
    """A file-selection (directory listing) view with no path field/browse button.

    The view renders the backend-driven directory listing only; it is meant to be
    embedded in any view container (or inside a :class:`FileChooserDialog`).  A
    path display, edit field, and browse button are intentionally not part of this
    view — compose those yourself (e.g. a :class:`TextFieldView` plus a
    :class:`ButtonView` that calls ``open_file_chooser``).
    """

    _node_type = "file_chooser_view"

    def __init__(
        self,
        cid: str,
        *,
        label: str = "",
        value: str = "",
        placeholder: str = "",
        root: str | None = None,
        accept: str = "",
        on_change: Handler | None = None,
        **kwargs: Any,
    ) -> None:
        kwargs.setdefault("min_width", Size.px(320))
        kwargs.setdefault("min_height", Size.px(240))
        kwargs.setdefault("preferred_width", Size.px(400))
        kwargs.setdefault("preferred_height", Size.px(320))
        super().__init__(cid, label=label, **kwargs)
        self.control = FileChooser(
            id=cid,
            label=label,
            tooltip=self.tooltip,
            value=value,
            placeholder=placeholder,
            root=root,
            accept=accept,
            on_change=on_change,
        )


class TextFieldView(ControlView):
    """A single-line text input control as a view."""

    _node_type = "text_field_view"

    def __init__(
        self,
        cid: str,
        *,
        label: str = "",
        value: str = "",
        placeholder: str = "",
        tooltip: str = "",
        on_change: Handler | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(cid, label=label, tooltip=tooltip, **kwargs)
        self.control = TextField(
            id=cid,
            label=label,
            tooltip=tooltip,
            value=value,
            placeholder=placeholder,
            on_change=on_change,
        )


class TextAreaView(ControlView):
    """A multi-line text input control as a view."""

    _node_type = "text_area_view"

    def __init__(
        self,
        cid: str,
        *,
        label: str = "",
        value: str = "",
        placeholder: str = "",
        rows: int = 4,
        tooltip: str = "",
        on_change: Handler | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(cid, label=label, tooltip=tooltip, **kwargs)
        self.control = TextArea(
            id=cid,
            label=label,
            tooltip=tooltip,
            value=value,
            placeholder=placeholder,
            rows=rows,
            on_change=on_change,
        )


class ColorPickerView(ControlView):
    """A color picker control as a view."""

    _node_type = "color_picker_view"

    def __init__(
        self,
        cid: str,
        *,
        label: str = "",
        value: str = "#ffffff",
        tooltip: str = "",
        on_change: Handler | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(cid, label=label, tooltip=tooltip, **kwargs)
        self.control = ColorPicker(
            id=cid,
            label=label,
            tooltip=tooltip,
            value=value,
            on_change=on_change,
        )


class CheckboxView(ControlView):
    """A boolean checkbox control as a view."""

    _node_type = "checkbox_view"

    def __init__(
        self,
        cid: str,
        *,
        label: str = "",
        variant: EControlVariant = EControlVariant.DEFAULT,
        value: bool = False,
        tooltip: str = "",
        on_change: Handler | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(cid, label=label, tooltip=tooltip, **kwargs)
        self.control = Checkbox(
            id=cid,
            label=label,
            tooltip=tooltip,
            variant=variant,
            value=value,
            on_change=on_change,
        )


class ValueEditView(ControlView):
    """A numeric stepper control as a view."""

    _node_type = "value_edit_view"

    def __init__(
        self,
        cid: str,
        *,
        label: str = "",
        min: float = 0.0,
        max: float = 1.0,
        step: float = 0.1,
        digits: int = 2,
        value: float = 0.0,
        editable: bool = True,
        tooltip: str = "",
        on_change: Handler | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(cid, label=label, tooltip=tooltip, **kwargs)
        self.control = ValueEdit(
            id=cid,
            label=label,
            tooltip=tooltip,
            min=float(min),
            max=float(max),
            step=float(step),
            digits=int(digits),
            value=float(value),
            editable=editable,
            on_change=on_change,
        )


class TableView(ControlView):
    """An editable tabular-data control rendered as a view."""

    _node_type = "table_view"

    def __init__(
        self,
        cid: str,
        *,
        label: str = "",
        columns: list[str] | tuple[str, ...] = (),
        rows: list[list[str]] | tuple[tuple[str, ...], ...] = (),
        allow_add_rows: bool = True,
        allow_add_columns: bool = True,
        allow_delete_rows: bool = True,
        max_history: int = 100,
        tooltip: str = "",
        on_cell_change: Handler | None = None,
        on_row_add: Handler | None = None,
        on_column_add: Handler | None = None,
        on_row_delete: Handler | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(cid, label=label, tooltip=tooltip, **kwargs)
        self.control = Table(
            id=cid,
            label=label,
            tooltip=tooltip,
            columns=list(columns),
            rows=[list(row) for row in rows],
            allow_add_rows=allow_add_rows,
            allow_add_columns=allow_add_columns,
            allow_delete_rows=allow_delete_rows,
            max_history=max_history,
            on_cell_change=on_cell_change,
            on_row_add=on_row_add,
            on_column_add=on_column_add,
            on_row_delete=on_row_delete,
        )

    def undo(self) -> bool:
        """Undo the last edit of the wrapped ``Table`` (model-only)."""
        return self.control.undo()

    def redo(self) -> bool:
        """Redo the last undone edit of the wrapped ``Table`` (model-only)."""
        return self.control.redo()

    @property
    def can_undo(self) -> bool:
        """Whether the wrapped ``Table`` can be undone."""
        return self.control.can_undo

    @property
    def can_redo(self) -> bool:
        """Whether the wrapped ``Table`` can be redone."""
        return self.control.can_redo


def control_to_view(ctrl: Control) -> ControlView:
    """Wrap an existing :class:`Control` in its ``*View`` counterpart.

    The returned view reuses *ctrl* as its ``control`` (the single source of
    truth), so backend updates via ``scene._controls`` and control handlers
    registered under the control id keep working.
    """
    if isinstance(ctrl, Slider):
        view = SliderView(
            ctrl.id,
            label=ctrl.label,
            tooltip=ctrl.tooltip,
            variant=ctrl.variant,
            min=ctrl.min,
            max=ctrl.max,
            step=ctrl.step,
            value=ctrl.value,
            on_change=ctrl.on_change,
        )
    elif isinstance(ctrl, Dropdown):
        view = DropdownView(
            ctrl.id,
            label=ctrl.label,
            tooltip=ctrl.tooltip,
            options=ctrl.options,
            value=ctrl.value,
            on_change=ctrl.on_change,
        )
    elif isinstance(ctrl, Button):
        view = ButtonView(
            ctrl.id,
            label=ctrl.label,
            tooltip=ctrl.tooltip,
            variant=ctrl.variant,
            icon=ctrl.icon,
            icon_only=ctrl.icon_only,
            on_click=ctrl.on_click,
        )
    elif isinstance(ctrl, Checkbox):
        view = CheckboxView(
            ctrl.id,
            label=ctrl.label,
            tooltip=ctrl.tooltip,
            variant=ctrl.variant,
            value=ctrl.value,
            on_change=ctrl.on_change,
        )
    elif isinstance(ctrl, TextField):
        view = TextFieldView(
            ctrl.id,
            label=ctrl.label,
            tooltip=ctrl.tooltip,
            value=ctrl.value,
            placeholder=ctrl.placeholder,
            on_change=ctrl.on_change,
        )
    elif isinstance(ctrl, TextArea):
        view = TextAreaView(
            ctrl.id,
            label=ctrl.label,
            tooltip=ctrl.tooltip,
            value=ctrl.value,
            placeholder=ctrl.placeholder,
            rows=ctrl.rows,
            on_change=ctrl.on_change,
        )
    elif isinstance(ctrl, ColorPicker):
        view = ColorPickerView(
            ctrl.id,
            label=ctrl.label,
            tooltip=ctrl.tooltip,
            value=ctrl.value,
            on_change=ctrl.on_change,
        )
    elif isinstance(ctrl, FileChooser):
        view = FileChooserView(
            ctrl.id,
            label=ctrl.label,
            tooltip=ctrl.tooltip,
            value=ctrl.value,
            placeholder=ctrl.placeholder,
            root=ctrl.root,
            accept=ctrl.accept,
            on_change=ctrl.on_change,
        )
    elif isinstance(ctrl, ValueEdit):
        view = ValueEditView(
            ctrl.id,
            label=ctrl.label,
            tooltip=ctrl.tooltip,
            min=ctrl.min,
            max=ctrl.max,
            step=ctrl.step,
            digits=ctrl.digits,
            value=ctrl.value,
            editable=ctrl.editable,
            on_change=ctrl.on_change,
        )
    elif isinstance(ctrl, Table):
        view = TableView(
            ctrl.id,
            label=ctrl.label,
            tooltip=ctrl.tooltip,
            columns=ctrl.columns,
            rows=ctrl.rows,
            allow_add_rows=ctrl.allow_add_rows,
            allow_add_columns=ctrl.allow_add_columns,
            on_cell_change=ctrl.on_cell_change,
            on_row_add=ctrl.on_row_add,
            on_column_add=ctrl.on_column_add,
        )
    else:
        raise TypeError(f"Unknown control kind: {type(ctrl).__name__}")
    view.control = ctrl  # reuse the same control object (source of truth)
    return view


def serialize_layout(
    root: View, name: str = "", overlay: list[View] | None = None
) -> dict[str, Any]:
    """Serialize a view tree to the ``view_layout`` message.

    ``overlay`` lists extra views (e.g. global menus) mounted into the global
    overlay container; they are serialized after the root with the same id
    generator so node ids stay unique across root and overlay.
    """
    id_gen = _make_id_gen()
    result = {
        "type": "view_layout",
        "name": name,
        "scenes": iter_scene_names(root),
        "root": root._serialize(id_gen),
    }
    if overlay:
        result["overlay"] = [view._serialize(id_gen) for view in overlay]
    return result


def iter_scene_names(root: View) -> list[str]:
    """Return the deduplicated scene names referenced by *root* (DFS order)."""
    names: list[str] = []
    seen: set[str] = set()

    def _visit(view: View) -> None:
        scene = getattr(view, "scene", None)
        if isinstance(scene, str) and scene not in seen:
            seen.add(scene)
            names.append(scene)
        for child in getattr(view, "children", None) or ():
            _visit(child)
        for child in getattr(view, "overlay", None) or ():
            _visit(child)

    _visit(root)
    return names


def iter_scene_views(root: View) -> Iterator[SceneView]:
    """Yield every :class:`SceneView` in the tree (DFS order)."""

    def _visit(view: View) -> Iterator[SceneView]:
        if isinstance(view, SceneView):
            yield view
        for child in getattr(view, "children", None) or ():
            yield from _visit(child)
        for child in getattr(view, "overlay", None) or ():
            yield from _visit(child)

    yield from _visit(root)


def iter_control_views(root: View) -> Iterator[ControlView]:
    """Yield every control view in the tree (DFS order)."""

    def _visit(view: View) -> Iterator[ControlView]:
        if isinstance(view, ControlView):
            yield view
        for child in getattr(view, "children", None) or ():
            yield from _visit(child)
        for child in getattr(view, "overlay", None) or ():
            yield from _visit(child)

    yield from _visit(root)


__all__ = [
    "ButtonView",
    "ControlView",
    "DropdownView",
    "FileChooserView",
    "GroupView",
    "MenuView",
    "SceneView",
    "SizeSpec",
    "SliderView",
    "SpacerView",
    "SplitView",
    "StackView",
    "TableView",
    "ValueEditView",
    "View",
    "control_to_view",
    "iter_control_views",
    "iter_scene_names",
    "iter_scene_views",
    "serialize_layout",
    "size_from_dict",
]
