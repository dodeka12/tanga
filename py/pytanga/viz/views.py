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

from ._controls import Handler
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
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        if direction not in ("vertical", "horizontal", "wrap"):
            raise ValueError(
                f"direction must be 'vertical', 'horizontal' or 'wrap', got {direction!r}"
            )
        self.direction = direction
        self.children = list(children or [])

    def _serialize(self, id_gen: Iterator[str]) -> dict[str, Any]:
        result = super()._serialize(id_gen)
        result["direction"] = self.direction
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
        position: str | None = None,
        collapsed: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(direction, children, **kwargs)
        self.title = title
        self.position = position
        self.collapsed = collapsed

    def _serialize(self, id_gen: Iterator[str]) -> dict[str, Any]:
        result = super()._serialize(id_gen)
        result["title"] = self.title
        result["position"] = self.position
        result["collapsed"] = self.collapsed
        return result


class ControlView(View):
    """Base for a single HTML control rendered as a plain ``View`` (no scene).

    The control ``id`` is the WebSocket event key (``control_id``) and must be
    unique across the app.
    """

    _node_type = "control"

    def __init__(self, cid: str, *, label: str = "", **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.id = cid
        self.label = label

    def _serialize(self, id_gen: Iterator[str]) -> dict[str, Any]:
        result = super()._serialize(id_gen)
        result["id"] = self.id  # control id doubles as the event key
        result["label"] = self.label
        return result


class SliderView(ControlView):
    """A numeric slider control as a view."""

    _node_type = "slider_view"

    def __init__(
        self,
        cid: str,
        *,
        label: str = "",
        min: float = 0.0,
        max: float = 1.0,
        step: float = 0.01,
        default: float | None = None,
        on_change: Handler | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(cid, label=label, **kwargs)
        self.min = float(min)
        self.max = float(max)
        self.step = float(step)
        self.default = self.min if default is None else float(default)
        self.on_change = on_change

    def _serialize(self, id_gen: Iterator[str]) -> dict[str, Any]:
        result = super()._serialize(id_gen)
        result["min"] = self.min
        result["max"] = self.max
        result["step"] = self.step
        result["default"] = self.default
        return result


class ButtonView(ControlView):
    """A clickable button control as a view."""

    _node_type = "button_view"

    def __init__(
        self,
        cid: str,
        *,
        label: str = "",
        on_click: Handler | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(cid, label=label, **kwargs)
        self.on_click = on_click


class DropdownView(ControlView):
    """A dropdown/select control as a view."""

    _node_type = "dropdown_view"

    def __init__(
        self,
        cid: str,
        *,
        label: str = "",
        options: list[str] | tuple[str, ...] = (),
        default: str = "",
        on_change: Handler | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(cid, label=label, **kwargs)
        self.options = list(options)
        self.default = default
        self.on_change = on_change

    def _serialize(self, id_gen: Iterator[str]) -> dict[str, Any]:
        result = super()._serialize(id_gen)
        result["options"] = self.options
        result["default"] = self.default
        return result


class FileChooserView(ControlView):
    """A file-path control (text field + backend file browser) as a view."""

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
        super().__init__(cid, label=label, **kwargs)
        self.value = value
        self.placeholder = placeholder
        self.root = root
        self.accept = accept
        self.on_change = on_change

    def _serialize(self, id_gen: Iterator[str]) -> dict[str, Any]:
        result = super()._serialize(id_gen)
        result["value"] = self.value
        result["placeholder"] = self.placeholder
        result["root"] = self.root
        result["accept"] = self.accept
        return result


def serialize_layout(root: View, name: str = "") -> dict[str, Any]:
    """Serialize a view tree to the ``view_layout`` message."""
    return {
        "type": "view_layout",
        "name": name,
        "scenes": iter_scene_names(root),
        "root": root._serialize(_make_id_gen()),
    }


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
    "SceneView",
    "SizeSpec",
    "SliderView",
    "SpacerView",
    "SplitView",
    "StackView",
    "View",
    "iter_control_views",
    "iter_scene_names",
    "serialize_layout",
    "size_from_dict",
]
