# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Scene-graph node classes for the Tanga 3D viewer.

The scene graph is the authoritative source of truth for objects in the
visualizer.  Each node carries a canonical :class:`Transform`, an independent
``dirty`` / ``transform_dirty`` flag pair, and can serialize itself.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import numpy as np

from ._styles import _style_for_kind
from ._transforms import rotation_matrix, scale_matrix, to_trs, translation_matrix

__all__ = ["Transform", "VizNode", "VizObject", "VizGroup", "resolve_style"]


class Transform:
    """A canonical TRS transform (position + Euler rotation + scale).

    Position and rotation are 3-tuples; ``rotation`` uses Euler angles in
    order ``"XYZ"`` (three.js default).  The 4×4 matrix is derived from the
    TRS via :mod:`pytanga.viz._transforms`.
    """

    def __init__(
        self,
        position=(0.0, 0.0, 0.0),
        rotation=(0.0, 0.0, 0.0),
        scale=(1.0, 1.0, 1.0),
    ) -> None:
        self.position = tuple(float(v) for v in position)
        self.rotation = tuple(float(v) for v in rotation)
        self.scale = tuple(float(v) for v in scale)

    def matrix(self) -> np.ndarray:
        """Return the 4×4 matrix derived from the canonical TRS."""
        rx = rotation_matrix((1, 0, 0), self.rotation[0])
        ry = rotation_matrix((0, 1, 0), self.rotation[1])
        rz = rotation_matrix((0, 0, 1), self.rotation[2])
        r = rx @ ry @ rz
        return translation_matrix(*self.position) @ r @ scale_matrix(*self.scale)

    def from_matrix(self, m: np.ndarray) -> "Transform":
        """Set TRS from a 4×4 matrix (decomposes via ``to_trs``)."""
        self.position, self.rotation, self.scale = to_trs(m)
        return self

    def set_matrix(self, m: np.ndarray) -> "Transform":
        """Alias for :meth:`from_matrix`."""
        return self.from_matrix(m)

    def apply_matrix(self, m: np.ndarray, space: str = "local") -> "Transform":
        """Apply a matrix in local or world space.

        ``"local"`` post-multiplies (``M_current @ M``); ``"world"``
        pre-multiplies (``M @ M_current``).
        """
        if space == "local":
            new = self.matrix() @ m
        elif space == "world":
            new = m @ self.matrix()
        else:
            raise ValueError(f"space must be 'local' or 'world', got {space!r}")
        self.position, self.rotation, self.scale = to_trs(new)
        return self

    def translate(self, x: float = 0.0, y: float = 0.0, z: float = 0.0) -> "Transform":
        """Translate the transform (world-space position delta)."""
        self.position = (
            self.position[0] + float(x),
            self.position[1] + float(y),
            self.position[2] + float(z),
        )
        return self

    def rotate(self, axis, angle: float) -> "Transform":
        """Rotate the transform about *axis* (local space)."""
        self.apply_matrix(rotation_matrix(axis, angle), space="local")
        return self

    def scale_by(
        self, x: float = 1.0, y: float | None = None, z: float | None = None
    ) -> "Transform":
        """Scale the transform (uniform when only *x* is given)."""
        if y is None and z is None:
            y = z = float(x)
        self.scale = (
            self.scale[0] * float(x),
            self.scale[1] * float(y),
            self.scale[2] * float(z),
        )
        return self

    def set(
        self,
        position=None,
        rotation=None,
        scale=None,
    ) -> "Transform":
        """Set TRS components; ``None`` leaves a component unchanged."""
        if position is not None:
            self.position = tuple(float(v) for v in position)
        if rotation is not None:
            self.rotation = tuple(float(v) for v in rotation)
        if scale is not None:
            self.scale = tuple(float(v) for v in scale)
        return self

    def to_dict(self) -> dict[str, list[float]]:
        """Serialize to a JSON-ready dict."""
        return {
            "position": list(self.position),
            "rotation": list(self.rotation),
            "scale": list(self.scale),
        }


class VizNode:
    """Base node in the scene graph.

    Subclasses set ``kind`` / ``layer``.  A node may be a leaf
    (:class:`VizObject`), a container (:class:`VizGroup`), or a generic
    overlay (annotation / title).
    """

    def __init__(
        self,
        id: str,
        *,
        name: str | None = None,
        layer: str = "scene",
        kind: str = "",
        parent: "VizNode | None" = None,
        transform: Transform | None = None,
        visible: bool = True,
        data: Any = None,
    ) -> None:
        self.id = id
        self.name = name if name is not None else id
        self.parent: VizNode | None = parent
        self.children: list[VizNode] = []
        self.transform = transform if transform is not None else Transform()
        self.visible = visible
        self.layer = layer
        self.kind = kind
        self.data = data
        self.dirty = True
        self.transform_dirty = True
        if parent is not None:
            parent.add_child(self)

    # -- Graph bookkeeping -----------------------------------

    def add_child(self, node: "VizNode") -> "VizNode":
        """Attach *node* as a child, reparenting it if necessary."""
        if node.parent is not None and node.parent is not self:
            node.parent.remove_child(node)
        node.parent = self
        if node not in self.children:
            self.children.append(node)
        return node

    def remove_child(self, node: "VizNode") -> None:
        """Detach *node* from this node's children."""
        if node in self.children:
            self.children.remove(node)
        if node.parent is self:
            node.parent = None

    def world_matrix(self) -> np.ndarray:
        """Return the world matrix (parent chain multiplication)."""
        m = self.transform.matrix()
        if self.parent is not None:
            m = self.parent.world_matrix() @ m
        return m

    # -- Mutators --------------------------------------------

    def set_transform(self, *, position=None, rotation=None, scale=None) -> "VizNode":
        """Set the node's transform; only ``transform_dirty`` becomes set."""
        self.transform.set(position=position, rotation=rotation, scale=scale)
        self.transform_dirty = True
        return self

    def update(self, **properties: Any) -> "VizNode":
        """Merge properties into the node and mark it dirty."""
        self.dirty = True
        return self

    # -- Serialization ----------------------------------------

    def serialize(self, styles_map: dict[str, Any] | None = None) -> dict[str, Any]:
        """Serialize the base node fields plus any overlay payload."""
        result: dict[str, Any] = {
            "id": self.id,
            "layer": self.layer,
            "kind": self.kind,
            "parent_id": self.parent.id if self.parent is not None else None,
            "transform": self.transform.to_dict(),
            "visible": self.visible,
        }
        if self.layer == "overlay":
            if self.kind == "annotation":
                result.update(_annotation_payload(self.data))
            elif self.kind == "title":
                result.update(_title_payload(self.data))
        return result


class VizObject(VizNode):
    """A drawable leaf node: resolved geometry + resolved style."""

    def __init__(
        self,
        id: str,
        *,
        kind: str = "",
        entity: Any = None,
        properties: dict[str, Any] | None = None,
        style: Any = None,
        layer: str = "scene",
        **kwargs: Any,
    ) -> None:
        super().__init__(id, kind=kind, layer=layer, **kwargs)
        self.entity = entity
        self.properties = dict(properties or {})
        self.style = style  # resolved style instance (canonical + user merge)

    # -- Data setters (mark ``dirty`` only) -------------------

    def set_entity(self, entity: Any) -> "VizObject":
        """Replace the geometry and mark the node dirty (not transform-dirty)."""
        self.entity = entity
        self.kind = type(entity).__name__
        self.dirty = True
        return self

    def set_style(self, style: Any) -> "VizObject":
        """Merge non-``None`` fields of *style* into the resolved style."""
        self._merge_style(style)
        self.dirty = True
        return self

    def set_color(self, color: Any) -> "VizObject":
        """Set the resolved color and mark dirty."""
        self.properties["color"] = color
        self._apply_color(color)
        self.dirty = True
        return self

    def set_opacity(self, opacity: float) -> "VizObject":
        """Set the resolved opacity and mark dirty."""
        self.properties["opacity"] = float(opacity)
        self._apply_opacity(float(opacity))
        self.dirty = True
        return self

    def set_texture_label(self, texture_label: Any) -> "VizObject":
        """Set the resolved texture label and mark dirty."""
        self._apply_texture_label(texture_label)
        self.dirty = True
        return self

    # -- Properties (resolved style getters) ------------------

    @property
    def color(self) -> Any:
        return getattr(self.style, "color", None)

    @property
    def opacity(self) -> float | None:
        return getattr(self.style, "opacity", None)

    @property
    def texture_label(self) -> Any:
        return getattr(self.style, "texture_label", None)

    # -- Update (backward-compat scene property merge) --------

    def update(self, **properties: Any) -> "VizObject":
        self.properties.update(properties)
        style = properties.get("style")
        if style is not None:
            self._merge_style(style)
        if "color" in properties:
            self._apply_color(properties["color"])
        if "opacity" in properties:
            self._apply_opacity(properties["opacity"])
        if "texture_label" in properties:
            self._apply_texture_label(properties["texture_label"])
        self.dirty = True
        return self

    # -- Serialization ----------------------------------------

    def serialize(self, styles_map: dict[str, Any] | None = None) -> dict[str, Any]:
        from .serializer import _serialize_label, serialize_entity

        if self.layer == "overlay" and self.kind == "label":
            d = _serialize_label(self.entity, self.id)
        else:
            d = serialize_entity(
                self.entity,
                self.id,
                self.properties,
                kind=self.kind,
                styles_map=styles_map,
            )
        d["parent_id"] = self.parent.id if self.parent is not None else None
        d["transform"] = self.transform.to_dict()
        d["visible"] = self.visible
        return d

    # -- Internals ---------------------------------------------

    def _merge_style(self, style: Any) -> None:
        if style is None:
            return
        if self.style is None:
            self.style = deepcopy(style)
            return
        for field, value in style.__dict__.items():
            if value is not None:
                setattr(self.style, field, value)

    def _apply_color(self, color: Any) -> None:
        if self.style is not None and hasattr(self.style, "color"):
            self.style.color = color

    def _apply_opacity(self, opacity: float) -> None:
        if self.style is not None and hasattr(self.style, "opacity"):
            self.style.opacity = opacity

    def _apply_texture_label(self, texture_label: Any) -> None:
        if self.style is not None and hasattr(self.style, "texture_label"):
            self.style.texture_label = deepcopy(texture_label)


class VizGroup(VizNode):
    """A container node (an "empty" transform with children)."""

    def __init__(self, id: str, *, name: str | None = None, **kwargs: Any) -> None:
        super().__init__(id, name=name, layer="scene", kind="VizGroup", **kwargs)


def resolve_style(
    kind: str,
    user_style: Any,
    props: dict[str, Any],
    styles_map: dict[str, Any] | None,
) -> Any:
    """Resolve the effective style instance for a kind at creation time.

    Starts from the canonical default for *kind*, merges the user style's
    non-``None`` fields, then overlays flat ``color`` / ``opacity`` props.
    """
    canonical = _style_for_kind(kind, styles_map=styles_map)
    resolved = deepcopy(canonical)
    if user_style is not None:
        for field, value in user_style.__dict__.items():
            if value is not None:
                setattr(resolved, field, value)
    if props.get("color") is not None and hasattr(resolved, "color"):
        resolved.color = props["color"]
    if props.get("opacity") is not None and hasattr(resolved, "opacity"):
        resolved.opacity = props["opacity"]
    return resolved


def _annotation_payload(data: Any) -> dict[str, Any]:
    text = data.get("text", "") if isinstance(data, dict) else ""
    style = data.get("style", {}) if isinstance(data, dict) else {}
    return {
        "positioning": "fixed",
        "anchor": "bottom",
        "text": text,
        "style": style,
    }


def _title_payload(data: Any) -> dict[str, Any]:
    text = data.get("text", "") if isinstance(data, dict) else ""
    style = data.get("style", {}) if isinstance(data, dict) else {}
    return {
        "positioning": "fixed",
        "anchor": "top",
        "text": text,
        "style": style,
    }