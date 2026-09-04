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

import json
from datetime import datetime, timezone
from enum import StrEnum
from itertools import count
from pathlib import Path
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
    Label,
    Markdown,
    Slider,
    Table,
    TextArea,
    TextField,
    ValueEdit,
)
from ._anchor import EAnchor
from ._icons import Icon
from ._size import Size, SizeSpec, size_from_dict
from .camera import CameraConfig, View2DConfig, View3dConfig, _normalize_camera_config

Orientation = Literal["horizontal", "vertical"]


class EStackDirection(StrEnum):
    VERTICAL = "vertical"
    HORIZONTAL = "horizontal"
    WRAP = "wrap"


class EStackAlign(StrEnum):
    START = "start"
    CENTER = "center"
    END = "end"
    STRETCH = "stretch"


class EStackJustify(StrEnum):
    START = "start"
    CENTER = "center"
    END = "end"
    SPACE_BETWEEN = "space-between"
    SPACE_AROUND = "space-around"
    SPACE_EVENLY = "space-evenly"


#: Default minimum extent for a scene pane on both axes, so a scene can never
#: be collapsed to nothing (override per view, or pass ``None`` to disable).
_DEFAULT_SCENE_MIN = Size.px(120)

#: Per-column horizontal floor for :class:`TableView` (px), so an N-column grid
#: keeps every column visible inside an auto-sized overlay panel.
_TABLE_COLUMN_MIN_PX = 60


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


#: Process-wide counter for auto-generated ``SceneView`` pane ids (``sv0``…).
#: A scene pane needs a stable id so it can be targeted at runtime
#: (``Visualizer.set_view_camera``) after the layout has been serialized.
_scene_view_counter = count()

#: Process-wide counter for auto-generated ``LogView`` ids (``log0``…).
_log_view_counter = count()

#: Process-wide counter for auto-generated ``View`` ids (``v0``…).  Every view
#: gets a stable id at construction so it can be addressed at runtime (e.g.
#: removed via ``Visualizer.remove_view``); a subclass may override it.
_view_counter = count()


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
        id: str | None = None,
        size: SizeSpec = None,
        preferred_width: SizeSpec = None,
        preferred_height: SizeSpec = None,
        min_width: SizeSpec = None,
        min_height: SizeSpec = None,
        max_width: SizeSpec = None,
        max_height: SizeSpec = None,
    ) -> None:
        self.id = id if id is not None else f"v{next(_view_counter)}"
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

    def _serialize(self) -> dict[str, Any]:
        """Serialize this node (subclasses append their type-specific fields)."""
        return {
            "type": self._node_type,
            "id": self.id,
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

    def _serialize(self) -> dict[str, Any]:
        result = super()._serialize()
        result["id"] = self.id
        result["scene"] = self.scene
        if self.camera is not None:
            result["camera"] = self.camera.to_dict()
        if self.overlay:
            result["children"] = [child._serialize() for child in self.overlay]
        return result


class SpacerView(View):
    """An empty, fully-flexible filler pane.

    A spacer grows to fill leftover space along a flow container's main axis:
    it defaults ``preferred_width``/``preferred_height`` to ``Size.fr(1)``,
    which the frontend maps to ``flex: 1 1 0``.  Inside a ``SplitView`` it is
    positioned absolutely, so the preferred size is inert there.
    """

    _node_type = "spacer"

    def __init__(self, **kwargs: Any) -> None:
        kwargs.setdefault("preferred_width", Size.fr(1))
        kwargs.setdefault("preferred_height", Size.fr(1))
        super().__init__(**kwargs)


#: Default gap (px) between a separator line and the adjacent content.
_DEFAULT_SEPARATOR_SPACING = 6


class SeparatorView(View):
    """A thin 1px divider line with spacing, for toolbars/menus/stacks.

    ``orientation`` describes the *line* (perpendicular to the container it
    lives in): ``"vertical"`` for a horizontal container (``ToolbarView`` /
    menu ``bar``) and ``"horizontal"`` for a vertical container
    (``StackView`` / ``MenuView`` dropdown).  ``"auto"`` (the default) lets the
    frontend container pick the perpendicular orientation; pin it explicitly
    where there is no enclosing ``StackView``-derived container to resolve it
    (e.g. a ``SplitView`` pane), in which case ``"auto"`` stays unresolved and
    renders nothing useful — so pass an explicit orientation there.

    ``spacing`` is the gap on each side of the line (default ``6`` px).
    """

    _node_type = "separator"

    def __init__(
        self,
        orientation: Literal["auto", "horizontal", "vertical"] = "auto",
        *,
        spacing: int | None = None,
        **kwargs: Any,
    ) -> None:
        if orientation not in ("auto", "horizontal", "vertical"):
            raise ValueError(
                f"orientation must be 'auto', 'horizontal' or 'vertical', "
                f"got {orientation!r}"
            )
        if spacing is not None and (
            isinstance(spacing, bool) or not isinstance(spacing, int) or spacing < 0
        ):
            raise ValueError(
                f"spacing must be a non-negative int or None, got {spacing!r}"
            )
        spacing = _DEFAULT_SEPARATOR_SPACING if spacing is None else spacing
        # The thin main-axis extent is just the 1px line; `spacing` is applied
        # as margin by the frontend.  For "auto" the frontend resolves
        # orientation and sets this itself.
        line = Size.px(1)
        if orientation == "vertical":
            kwargs.setdefault("preferred_width", line)
        elif orientation == "horizontal":
            kwargs.setdefault("preferred_height", line)
        super().__init__(**kwargs)
        self.orientation = orientation
        self.spacing = spacing

    def _serialize(self) -> dict[str, Any]:
        result = super()._serialize()
        result["orientation"] = self.orientation
        result["spacing"] = self.spacing
        return result


class LogView(View):
    """A live two-column (time | message) log rendered as a scrollable ``View``.

    Lines are appended from the backend via :meth:`log` and pushed to the
    frontend as ``log_update`` messages.  Each line is a dict with a UTC
    ``"time"`` key; string messages are stored under ``"message"`` and dict
    messages have their keys folded in.

    ``id`` is an optional stable identifier (auto-generated as ``"logN"`` when
    omitted); it is the key used to address this view at runtime.  ``max_history``
    caps the retained line count (FIFO drop-oldest); ``None`` keeps everything.
    """

    _node_type = "log_view"

    def __init__(
        self,
        id: str | None = None,
        *,
        max_history: int | None = None,
        **kwargs: Any,
    ) -> None:
        kwargs.setdefault("min_width", Size.px(200))
        kwargs.setdefault("min_height", Size.px(120))
        super().__init__(**kwargs)
        self.id = id if id is not None else f"log{next(_log_view_counter)}"
        if max_history is not None and (
            not isinstance(max_history, int) or max_history < 0
        ):
            raise ValueError("max_history must be None or a non-negative integer")
        self.max_history = max_history
        self.lines: list[dict[str, Any]] = []
        self._push = None  # callback slot injected by the Visualizer

    def log(self, message: Any) -> None:
        """Append *message* as a new line (str → ``{"message": …}``; dict → folded)."""
        line: dict[str, Any] = {"time": datetime.now(timezone.utc).isoformat()}
        if isinstance(message, dict):
            line.update(message)
        else:
            line["message"] = str(message)
        self.lines.append(line)
        if self.max_history is not None and len(self.lines) > self.max_history:
            del self.lines[: len(self.lines) - self.max_history]
        if self._push is not None:
            self._push(self.id, "append", [dict(line)])

    def get_log(self) -> list[dict[str, Any]]:
        """Return a copy of the current lines."""
        return [dict(line) for line in self.lines]

    def write_file(self, path: str | Path) -> None:
        """Write the current lines as JSON lines (one dict per line)."""
        Path(path).write_text(
            "".join(json.dumps(line) + "\n" for line in self.lines),
            encoding="utf-8",
        )

    def load_file(self, path: str | Path) -> None:
        """Replace the current lines with those read from a JSON-lines file."""
        raw = Path(path).read_text(encoding="utf-8")
        lines = [json.loads(line) for line in raw.splitlines() if line.strip()]
        if self.max_history is not None:
            lines = lines[-self.max_history :]
        self.lines = lines
        if self._push is not None:
            self._push(self.id, "replace", [dict(line) for line in self.lines])

    def clear(self) -> None:
        """Drop every line."""
        self.lines = []
        if self._push is not None:
            self._push(self.id, "clear")

    def _serialize(self) -> dict[str, Any]:
        result = super()._serialize()
        result["id"] = self.id
        result["max_history"] = self.max_history
        result["lines"] = [dict(line) for line in self.lines]
        return result


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

    def _serialize(self) -> dict[str, Any]:
        result = super()._serialize()
        result["orientation"] = self.orientation
        result["movable"] = self.movable
        result["sizes"] = (
            [_size_dict(s) for s in self.sizes]
            if self.sizes is not None
            else [None] * len(self.children)
        )
        result["children"] = [child._serialize() for child in self.children]
        return result


class StackView(View):
    """A flow container that stacks children vertically, horizontally, or wraps.

    Unlike :class:`SplitView`, children flow in normal document order (no
    splitters) and the container sizes to its content along the stack axis.
    """

    _node_type = "stack"

    def __init__(
        self,
        direction: EStackDirection,
        children: list[View] | None = None,
        *,
        scrollable: bool = False,
        gap: int | None = None,
        align: EStackAlign = EStackAlign.STRETCH,
        justify: EStackJustify = EStackJustify.START,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        if direction not in EStackDirection:
            raise ValueError(
                f"direction must be 'vertical', 'horizontal' or 'wrap', got {direction!r}"
            )
        if align not in EStackAlign:
            raise ValueError(
                f"align must be 'start', 'center', 'end' or 'stretch', got {align!r}"
            )
        if justify not in EStackJustify:
            raise ValueError(
                f"justify must be one of 'start', 'center', 'end', 'space-between', "
                f"'space-around', 'space-evenly', got {justify!r}"
            )
        if gap is not None and (
            isinstance(gap, bool) or not isinstance(gap, int) or gap < 0
        ):
            raise ValueError(f"gap must be a non-negative int or None, got {gap!r}")
        self.direction = direction
        self.children = list(children or [])
        self.scrollable = scrollable
        self.gap = gap
        self.align = align
        self.justify = justify

    def _serialize(self) -> dict[str, Any]:
        result = super()._serialize()
        result["direction"] = self.direction
        result["scrollable"] = self.scrollable
        result["gap"] = self.gap
        result["align"] = self.align
        result["justify"] = self.justify
        result["children"] = [child._serialize() for child in self.children]
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
        direction: EStackDirection = EStackDirection.VERTICAL,
        position: EAnchor | None = None,
        collapsed: bool = False,
        scrollable: bool = False,
        gap: int | None = None,
        align: EStackAlign = EStackAlign.STRETCH,
        justify: EStackJustify = EStackJustify.START,
        icon: Icon | None = None,
        icon_only: bool = False,
        tooltip: str = "",
        parent_id: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            direction,
            children,
            scrollable=scrollable,
            gap=gap,
            align=align,
            justify=justify,
            **kwargs,
        )
        self.title = title
        self.position = position
        self.collapsed = collapsed
        self.icon = icon
        self.icon_only = icon_only
        self.tooltip = tooltip
        self.parent_id = parent_id

    def _serialize(self) -> dict[str, Any]:
        result = super()._serialize()
        result["title"] = self.title
        result["position"] = self.position
        result["collapsed"] = self.collapsed
        if self.icon is not None:
            result["icon"] = str(self.icon)
        result["icon_only"] = self.icon_only
        if self.tooltip:
            result["tooltip"] = self.tooltip
        if self.parent_id is not None:
            result["parent_id"] = self.parent_id
        return result


class ToolbarView(StackView):
    """A horizontal control toolbar (a bordered :class:`StackView` row).

    ``direction`` is fixed to ``"horizontal"``.  ``margin`` is the inner
    spacing (padding) between the border and the controls; ``border`` toggles
    the thin outline.  ``gap`` spaces the controls, ``align`` sets cross-axis
    (vertical) alignment, and ``justify`` positions the controls along the row
    (``START`` left, ``END`` right, ``CENTER`` block-centered, ``SPACE_EVENLY``
    equally spaced).
    """

    _node_type = "toolbar"

    def __init__(
        self,
        children: list[View] | None = None,
        *,
        margin: SizeSpec = Size.px(6),
        border: bool = True,
        gap: int | None = None,
        align: EStackAlign = EStackAlign.CENTER,
        justify: EStackJustify = EStackJustify.START,
        **kwargs: Any,
    ) -> None:
        if margin is not None and not isinstance(margin, Size):
            raise ValueError(f"margin must be a Size or None, got {margin!r}")
        if not isinstance(border, bool):
            raise ValueError(f"border must be a bool, got {border!r}")
        super().__init__(
            "horizontal",
            children,
            gap=gap,
            align=align,
            justify=justify,
            **kwargs,
        )
        self.margin = margin
        self.border = border
        _apply_toolbar_variant(self)

    def _serialize(self) -> dict[str, Any]:
        result = super()._serialize()
        result["margin"] = _size_dict(self.margin)
        result["border"] = self.border
        return result


def _apply_toolbar_variant(view: View) -> None:
    """Recursively force ``TOOLBAR`` onto eligible control views in a toolbar."""
    for child in getattr(view, "children", None) or ():
        if isinstance(child, MenuView):
            continue  # a nested menu keeps its own MENU styling
        ctrl = getattr(child, "control", None)
        if ctrl is not None and hasattr(ctrl, "variant"):
            ctrl.variant = EControlVariant.TOOLBAR
        _apply_toolbar_variant(child)


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
        direction: EStackDirection | None = None,
        position: EAnchor | None = None,
        override_variant: bool = True,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        if mode not in ("dropdown", "bar"):
            raise ValueError(f"mode must be 'dropdown' or 'bar', got {mode!r}")
        if direction is None:
            direction = "horizontal" if mode == "bar" else "vertical"
        if direction not in EStackDirection:
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

    def _serialize(self) -> dict[str, Any]:
        result = super()._serialize()
        result["trigger_icon"] = (
            str(self.trigger_icon) if self.trigger_icon is not None else None
        )
        result["label"] = self.label
        result["mode"] = self.mode
        result["direction"] = self.direction
        result["position"] = self.position
        result["children"] = [child._serialize() for child in self.children]
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
        kwargs.setdefault("min_width", Size.px(120))
        kwargs.setdefault("min_height", Size.px(32))
        super().__init__(**kwargs)
        self.id = cid
        self.label = label
        self.tooltip = tooltip
        self.control: Control | None = None
        self._push = None  # callback slot injected at mount (LogView pattern)

    def __getattr__(self, name: str) -> Any:
        ctrl = self.__dict__.get("control")
        if ctrl is not None and hasattr(ctrl, name):
            return getattr(ctrl, name)
        raise AttributeError(f"{type(self).__name__} object has no attribute {name!r}")

    def set_value(self, value: Any) -> None:
        """Set this control's value and push ``control_update`` to the browser.

        Mutates ``self.control`` and, when mounted, pushes the new value through
        the injected ``_push`` callback (so backend-initiated changes reach the
        rendered DOM).
        """
        self.control.set_value(value)
        if self._push is not None:
            self._push(self.id, self.control.get_value())

    def _serialize(self) -> dict[str, Any]:
        result = super()._serialize()
        result["id"] = self.id  # control id doubles as the event key
        result["label"] = self.label
        result["tooltip"] = self.tooltip
        for key, val in self.control.serialize().items():
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
        on_press: Handler | None = None,
        on_release: Handler | None = None,
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
            on_press=on_press,
            on_release=on_release,
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
        if icon_only:
            # Icon-only buttons render as a small square tile; size the view to
            # match instead of the generic control floor (120×32) so adjacent
            # icons don't get a large empty gap around them.
            kwargs.setdefault("min_width", Size.px(28))
            kwargs.setdefault("min_height", Size.px(28))
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
        variant: EControlVariant = EControlVariant.DEFAULT,
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
            variant=variant,
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


class LabelView(ControlView):
    """A read-only text label control (configurable font size) as a view."""

    _node_type = "label_view"

    def __init__(
        self,
        cid: str,
        *,
        value: str = "",
        font_size: float = 14,
        **kwargs: Any,
    ) -> None:
        super().__init__(cid, **kwargs)
        self.control = Label(
            id=cid,
            label="",
            tooltip=self.tooltip,
            value=value,
            font_size=float(font_size),
        )


class MarkdownView(ControlView):
    """A read-only rendered-markdown control (with KaTeX math) as a view."""

    _node_type = "markdown_view"

    def __init__(
        self,
        cid: str,
        *,
        value: str = "",
        **kwargs: Any,
    ) -> None:
        super().__init__(cid, **kwargs)
        self.control = Markdown(
            id=cid,
            label="",
            tooltip=self.tooltip,
            value=value,
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
        on_change: Handler | None = None,
        **kwargs: Any,
    ) -> None:
        # A Tabulator grid needs horizontal room for every column; default the
        # min width to a per-column estimate so an auto-sized overlay panel
        # doesn't clip the last column.  An explicit ``min_width=`` still wins.
        ncols = max(1, len(columns))
        kwargs.setdefault("min_width", Size.px(max(120, ncols * _TABLE_COLUMN_MIN_PX)))
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
            on_change=on_change,
        )

    def undo(self) -> bool:
        """Undo the last edit of the wrapped ``Table`` and push the grid."""
        changed = self.control.undo()
        if changed:
            self._push_value()
        return changed

    def redo(self) -> bool:
        """Redo the last undone edit of the wrapped ``Table`` and push the grid."""
        changed = self.control.redo()
        if changed:
            self._push_value()
        return changed

    def _push_value(self) -> None:
        """Push the wrapped ``Table``'s grid to the browser (if mounted)."""
        if self._push is not None:
            self._push(self.id, self.control.get_value())

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
            on_press=ctrl.on_press,
            on_release=ctrl.on_release,
        )
    elif isinstance(ctrl, Dropdown):
        view = DropdownView(
            ctrl.id,
            label=ctrl.label,
            tooltip=ctrl.tooltip,
            variant=ctrl.variant,
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
            allow_delete_rows=ctrl.allow_delete_rows,
            max_history=ctrl.max_history,
            on_cell_change=ctrl.on_cell_change,
            on_row_add=ctrl.on_row_add,
            on_column_add=ctrl.on_column_add,
            on_row_delete=ctrl.on_row_delete,
            on_change=ctrl.on_change,
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
    result = {
        "type": "view_layout",
        "name": name,
        "scenes": iter_scene_names(root),
        "root": root._serialize(),
    }
    if overlay:
        result["overlay"] = [view._serialize() for view in overlay]
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


def iter_log_views(root: View) -> Iterator[LogView]:
    """Yield every :class:`LogView` in the tree (DFS order)."""

    def _visit(view: View) -> Iterator[LogView]:
        if isinstance(view, LogView):
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
    "LabelView",
    "LogView",
    "MarkdownView",
    "MenuView",
    "SceneView",
    "SeparatorView",
    "SizeSpec",
    "SliderView",
    "SpacerView",
    "SplitView",
    "StackView",
    "TableView",
    "ToolbarView",
    "ValueEditView",
    "View",
    "control_to_view",
    "iter_control_views",
    "iter_log_views",
    "iter_scene_names",
    "iter_scene_views",
    "serialize_layout",
    "size_from_dict",
]
