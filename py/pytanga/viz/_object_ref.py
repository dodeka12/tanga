# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Convenience reference class for mutating scene-graph nodes without tracking raw IDs."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pytanga.geometry.operators import Translator

from ._nodes import VizGroup, VizNode, VizOverlayObject, VizSceneObject, _style_to_dict

if TYPE_CHECKING:
    from ._scene_handle import VizSceneHandle


class VizObjectRef:
    """A convenience wrapper around a :class:`VizNode` and its scene handle.

    Property setters delegate to the node and mark the correct dirty aspect
    (``full`` / ``style`` / ``transform``).
    """

    def __init__(self, handle: "VizSceneHandle", node: VizNode) -> None:
        self._handle = handle
        self._node = node

    # ── Identity & access ─────────────────────────────────────

    @property
    def id(self) -> str:
        return self._node.id

    @property
    def name(self) -> str:
        return self._node.name

    @name.setter
    def name(self, value: str) -> None:
        self._node.name = value

    @property
    def layer(self) -> str:
        return self._node.layer

    @property
    def scene(self):
        return self._handle.scene

    @property
    def handle(self) -> "VizSceneHandle":
        return self._handle

    @property
    def scene_name(self) -> str:
        return self._handle.name

    @property
    def node(self) -> VizNode:
        return self._node

    @property
    def parent(self) -> "VizObjectRef | None":
        node = self._node
        if isinstance(node, VizSceneObject) and node.parent is not None:
            return VizObjectRef(self._handle, node.parent)
        return None

    @parent.setter
    def parent(self, value: Any) -> None:
        node = self._scene_node()
        if value is None:
            if node.parent is not None:
                node.parent.remove_child(node)
            return
        other = value._node if isinstance(value, VizObjectRef) else value
        if not isinstance(other, VizSceneObject):
            raise TypeError("parent must be a scene-layer node or VizObjectRef")
        other.add_child(node)

    # ── Data getters / setters ────────────────────────────────

    @property
    def entity(self) -> Any:
        node = self._node
        return node.entity if isinstance(node, VizSceneObject) else None

    @entity.setter
    def entity(self, value: Any) -> None:
        self._scene_node().set_entity(value)

    @property
    def style(self) -> Any:
        return self._node.style

    @style.setter
    def style(self, value: Any) -> None:
        self._node.set_style(value)

    @property
    def color(self) -> Any:
        return _style_to_dict(self._node.style).get("color")

    @color.setter
    def color(self, value: Any) -> None:
        self._node.set_color(value)

    @property
    def opacity(self) -> Any:
        return _style_to_dict(self._node.style).get("opacity")

    @opacity.setter
    def opacity(self, value: Any) -> None:
        self._node.set_opacity(value)

    @property
    def texture_label(self) -> Any:
        node = self._node
        if isinstance(node, VizSceneObject):
            return _style_to_dict(node.style).get("texture_label")
        return None

    @texture_label.setter
    def texture_label(self, value: Any) -> None:
        node = self._node
        if isinstance(node, VizSceneObject):
            node.set_texture_label(value)
        else:
            node.set_style({"texture_label": value})

    # ── Overlay-specific ─────────────────────────────────────

    @property
    def text(self) -> Any:
        return self._overlay_node().payload

    @text.setter
    def text(self, value: Any) -> None:
        self._overlay_node().set_payload(value)

    @property
    def payload(self) -> Any:
        return self._overlay_node().payload

    @payload.setter
    def payload(self, value: Any) -> None:
        self._overlay_node().set_payload(value)

    @property
    def position(self) -> tuple[float, float, float]:
        return self._overlay_node().position

    @position.setter
    def position(self, value: Any) -> None:
        self._overlay_node().set_position(value)

    @property
    def attach_to(self) -> str | None:
        return self._overlay_node().attach_to

    @attach_to.setter
    def attach_to(self, value: str | None) -> None:
        self._overlay_node().set_attach_to(value)

    @property
    def label_ids(self) -> list[str]:
        return self._handle.get_label_ids(self.id)

    @property
    def labels(self) -> list["VizObjectRef"]:
        scene = self._handle.scene
        return [VizObjectRef(self._handle, scene.get_node(lid)) for lid in self.label_ids]

    def update_label(self, text: str | None = None, style: Any | None = None) -> None:
        self._handle.update_label(self.id, text=text, style=style)

    # ── Transforms (scene nodes only) ─────────────────────────

    @property
    def transform(self):
        return self._scene_node().transform

    @property
    def world_matrix(self):
        return self._scene_node().world_matrix()

    def translate(self, x: Any = 0.0, y: float = 0.0, z: float = 0.0) -> None:
        node = self._scene_node()
        if isinstance(x, Translator):
            node.translate(x.vector.x, x.vector.y, x.vector.z)
        else:
            node.translate(x, y, z)

    def rotate(self, angle: float, axis: Any) -> None:
        self._scene_node().rotate(axis, angle)

    def scale_by(
        self, x: float = 1.0, y: float | None = None, z: float | None = None
    ) -> None:
        self._scene_node().scale_by(x, y, z)

    def set_transform(
        self,
        position: Any = None,
        rotation: Any = None,
        scale: Any = None,
    ) -> None:
        self._scene_node().set_transform(position=position, rotation=rotation, scale=scale)

    def apply_transform(self, op: Any) -> None:
        self._scene_node().apply_transform(op)

    # ── Graph (group refs) ────────────────────────────────────

    def add(self, obj: Any = None, **kwargs: Any) -> str:
        group = self._group_node()
        oid = self._handle.add(obj, **kwargs)
        child = self._handle.scene.get_node(oid)
        if isinstance(child, VizSceneObject):
            group.add_child(child)
        return oid

    def new(self, obj: Any = None, **kwargs: Any) -> "VizObjectRef":
        group = self._group_node()
        oid = self._handle.add(obj, **kwargs)
        child = self._handle.scene.get_node(oid)
        if isinstance(child, VizSceneObject):
            group.add_child(child)
        return VizObjectRef(self._handle, child)

    def add_group(self, name: str | None = None) -> "VizObjectRef":
        group = self._group_node()
        child = self._handle.scene.add_group(name)
        group.add_child(child)
        return VizObjectRef(self._handle, child)

    # ── Lifecycle / passthroughs ─────────────────────────────

    def update(self, **properties: Any) -> None:
        self._handle.update(self.id, **properties)

    def remove(self) -> None:
        self._handle.remove(self.id)

    def flush(self, *, fit_camera: bool = False) -> None:
        self._handle.flush(fit_camera=fit_camera)

    def animate_to(self, **kwargs: Any) -> None:
        self._handle.animate_to(self.id, **kwargs)

    def set_interaction(self, config: Any) -> None:
        self._handle.set_interaction(self.id, config)

    def on_interaction(self, event_type: Any, handler: Any) -> None:
        self._handle.on_interaction(self.id, event_type, handler)

    # ── Helpers ──────────────────────────────────────────────

    def _scene_node(self) -> VizSceneObject:
        if isinstance(self._node, VizSceneObject):
            return self._node
        raise TypeError(f"Operation requires a scene-layer node, got {self._node.kind!r}")

    def _overlay_node(self) -> VizOverlayObject:
        if isinstance(self._node, VizOverlayObject):
            return self._node
        raise TypeError(f"Operation requires an overlay node, got {self._node.kind!r}")

    def _group_node(self) -> VizGroup:
        if isinstance(self._node, VizGroup):
            return self._node
        raise TypeError(f"Operation requires a VizGroup node, got {self._node.kind!r}")

