# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Scene-graph node classes for the Tanga 3D viewer.

Node hierarchy:

- :class:`Transform` — canonical TRS (translation + Euler-``"XYZ"`` rotation +
  scale) with a derived 4×4 matrix and mutators.
- :class:`VizNode` — base node (id/name/layer/kind/visible) with aspect-dirty
  tracking.
- :class:`VizSceneObject` — scene-layer node carrying an entity, a resolved
  style, a :class:`Transform`, and a parent/child graph.
- :class:`VizOverlayObject` — overlay-layer node (label/annotation/title)
  carrying a ``position`` anchor, an optional ``attach_to`` scene-node
  reference, and a resolved style — **no** :class:`Transform`.
- :class:`VizGroup` — a :class:`VizSceneObject` container with no
  entity/style, ``kind == "VizGroup"``.
"""

from __future__ import annotations

from copy import copy
from typing import Any

import numpy as np

from . import _transforms as _T
from ._style_dict import _merge_style


def _as_vec3(value: Any) -> tuple[float, float, float]:
    """Best-effort convert *value* to a 3-vector of floats.

    Accepts objects with ``x``/``y``/``z`` attributes (``Point``,
    ``Direction``, …) or any 3-sequence.
    """
    if hasattr(value, "x") and hasattr(value, "y") and hasattr(value, "z"):
        return (float(value.x), float(value.y), float(value.z))
    seq = tuple(value)
    if len(seq) != 3:
        raise ValueError(f"Expected a 3-vector, got {value!r}")
    return (float(seq[0]), float(seq[1]), float(seq[2]))


def _is_vector_like(value: Any) -> bool:
    """Return ``True`` for non-scalar 3-vectors (tuples/lists/entity-like)."""
    if isinstance(value, (int, float, np.integer, np.floating)):
        return False
    return hasattr(value, "__len__") or (
        hasattr(value, "x") and hasattr(value, "y") and hasattr(value, "z")
    )


def _assign_style_field(style: Any, key: str, value: Any) -> Any:
    """Return a copy of *style* with ``style[key]``/``style.key`` set to *value*.

    Handles dict- and instance-backed resolved styles uniformly.
    """
    if isinstance(style, dict):
        result = copy(style)
        result[key] = value
        return result
    if style is not None and hasattr(style, key):
        result = copy(style)
        setattr(result, key, value)
        return result
    return style


def _merge_style_into(base: Any, override: Any) -> Any:
    """Merge a style override (instance or dict) onto *base* (non-``None``).

    Returns a new resolved style.  ``base`` may be ``None``, a style instance,
    or a dict.
    """
    if override is None:
        return base
    if isinstance(override, dict):
        if base is None:
            return copy(override)
        if isinstance(base, dict):
            result = copy(base)
            for key, value in override.items():
                if value is not None:
                    result[key] = value
            return result
        result = copy(base)
        for key, value in override.items():
            if value is not None and hasattr(result, key):
                setattr(result, key, value)
        return result
    # override is a style instance
    if base is None or isinstance(base, dict):
        return copy(override)
    return _merge_style(base, override, deep=True)


def _style_to_dict(style: Any) -> dict[str, Any]:
    """Return *style* as a plain dict (from an instance, a dict, or ``None``)."""
    if style is None:
        return {}
    if isinstance(style, dict):
        return dict(style)
    if hasattr(style, "to_dict"):
        return dict(style.to_dict())
    return dict(getattr(style, "__dict__", {}))


class Transform:
    """Canonical TRS transform (translation, Euler-``"XYZ"`` rotation, scale).

    Position and rotation are stored as Euler triples; the rotation order is
    ``"XYZ"`` (three.js default), i.e. ``R = Rx @ Ry @ Rz``.  The 4×4 matrix
    is derived on demand and used for composition/decomposition only.
    """

    def __init__(
        self,
        position: Any = (0.0, 0.0, 0.0),
        rotation: Any = (0.0, 0.0, 0.0),
        scale: Any = (1.0, 1.0, 1.0),
    ) -> None:
        self.position: tuple[float, float, float] = _as_vec3(position)
        self.rotation: tuple[float, float, float] = _as_vec3(rotation)
        self.scale: tuple[float, float, float] = _as_vec3(scale)

    def matrix(self) -> np.ndarray:
        """Return the derived 4×4 transform matrix ``T @ R @ S``."""
        rx = _T.rotation_matrix((1.0, 0.0, 0.0), self.rotation[0])
        ry = _T.rotation_matrix((0.0, 1.0, 0.0), self.rotation[1])
        rz = _T.rotation_matrix((0.0, 0.0, 1.0), self.rotation[2])
        r = rx @ ry @ rz
        return (
            _T.translation_matrix(*self.position)
            @ r
            @ _T.scale_matrix(*self.scale)
        )

    def set_matrix(self, m: Any) -> "Transform":
        """Set position/rotation/scale from a 4×4 matrix (decompose)."""
        pos, euler, scale = _T.to_trs(np.asarray(m, dtype=np.float64))
        self.position = pos
        self.rotation = euler
        self.scale = scale
        return self

    def from_matrix(self, m: Any) -> "Transform":
        """Alias for :meth:`set_matrix`."""
        return self.set_matrix(m)

    def apply_matrix(self, m: Any, space: str = "local") -> "Transform":
        """Compose with *m* in local or world space.

        ``"local"`` post-multiplies (``M_new = M @ m``); ``"world"``
        pre-multiplies (``M_new = m @ M``).  The result is decomposed back to
        TRS.
        """
        m = np.asarray(m, dtype=np.float64)
        if space == "local":
            return self.set_matrix(self.matrix() @ m)
        if space == "world":
            return self.set_matrix(m @ self.matrix())
        raise ValueError(f"Unknown space {space!r}; expected 'local' or 'world'")

    def translate(self, x: Any = 0.0, y: float = 0.0, z: float = 0.0) -> "Transform":
        """Translate by ``(x, y, z)``, or by a 3-vector supplied as *x*."""
        if _is_vector_like(x):
            dx, dy, dz = _as_vec3(x)
        else:
            dx, dy, dz = float(x), float(y), float(z)
        self.position = (
            self.position[0] + dx,
            self.position[1] + dy,
            self.position[2] + dz,
        )
        return self

    def rotate(self, axis: Any, angle: float) -> "Transform":
        """Rotate in local space by *angle* about *axis* (axis-angle)."""
        self.apply_matrix(_T.rotation_matrix(axis, angle), space="local")
        return self

    def scale_by(
        self,
        x: float = 1.0,
        y: float | None = None,
        z: float | None = None,
    ) -> "Transform":
        """Scale component-wise (or uniformly when only *x* is given)."""
        if y is None and z is None:
            sx = sy = sz = float(x)
        else:
            sx = float(x)
            sy = float(y if y is not None else 1.0)
            sz = float(z if z is not None else 1.0)
        self.scale = (
            self.scale[0] * sx,
            self.scale[1] * sy,
            self.scale[2] * sz,
        )
        return self

    def set(
        self,
        position: Any = None,
        rotation: Any = None,
        scale: Any = None,
    ) -> "Transform":
        """Set position / rotation / scale (only the provided components)."""
        if position is not None:
            self.position = _as_vec3(position)
        if rotation is not None:
            self.rotation = _as_vec3(rotation)
        if scale is not None:
            self.scale = _as_vec3(scale)
        return self

    def to_dict(self) -> dict[str, Any]:
        """Return the JSON-ready TRS dict."""
        return {
            "position": list(self.position),
            "rotation": list(self.rotation),
            "scale": list(self.scale),
        }


class VizNode:
    """Base scene-graph node with aspect-dirty tracking."""

    def __init__(
        self,
        id: str,
        *,
        name: str = "",
        layer: str = "scene",
        kind: str = "",
        visible: bool = True,
    ) -> None:
        self.id: str = id
        self.name: str = name
        self.layer: str = layer
        self.kind: str = kind
        self.visible: bool = visible
        self._dirty_aspects: set[str] = {"full"}

    # ── Aspect tracking ─────────────────────────────────────

    def mark(self, kind: str = "full") -> None:
        """Set a dirty aspect.  ``"full"`` clears the other aspects."""
        if kind == "full":
            self._dirty_aspects = {"full"}
        else:
            self._dirty_aspects.discard("full")
            self._dirty_aspects.add(kind)

    def dirty_for(self, aspect: str) -> bool:
        """Return whether *aspect* is dirty."""
        return aspect in self._dirty_aspects

    def consume_dirty(self) -> set[str]:
        """Return and clear the dirty aspects."""
        dirty = set(self._dirty_aspects)
        self._dirty_aspects.clear()
        return dirty

    def serialize(self) -> dict[str, Any]:
        """Serialize the base node fields."""
        return {
            "id": self.id,
            "layer": self.layer,
            "kind": self.kind,
            "visible": self.visible,
        }


class VizSceneObject(VizNode):
    """Scene-layer node: entity + resolved style + transform + parent/child."""

    def __init__(
        self,
        id: str,
        entity: Any,
        style: Any = None,
        *,
        name: str = "",
        kind: str | None = None,
        transform: Transform | None = None,
        parent: "VizSceneObject | None" = None,
        visible: bool = True,
        props: dict[str, Any] | None = None,
        styles_map: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            id,
            name=name,
            layer="scene",
            kind=kind if kind is not None else (type(entity).__name__ if entity is not None else ""),
            visible=visible,
        )
        self.entity: Any = entity
        self.style: Any = style
        self.transform: Transform = transform if transform is not None else Transform()
        self.parent: VizSceneObject | None = None
        self.children: list[VizSceneObject] = []
        self._props: dict[str, Any] = dict(props) if props else {}
        self._styles_map: dict[str, Any] | None = styles_map
        if parent is not None:
            parent.add_child(self)

    # ── Parent/child graph ──────────────────────────────────

    def add_child(self, node: "VizSceneObject") -> None:
        """Attach *node* as a child (re-parenting if needed)."""
        if node.parent is not None and node.parent is not self:
            node.parent.remove_child(node)
        node.parent = self
        if node not in self.children:
            self.children.append(node)

    def remove_child(self, node: "VizSceneObject") -> None:
        """Detach *node* from this parent."""
        if node in self.children:
            self.children.remove(node)
        node.parent = None

    def world_matrix(self) -> np.ndarray:
        """Return this node's world transform matrix (parent chain composed)."""
        m = self.transform.matrix()
        if self.parent is not None:
            m = self.parent.world_matrix() @ m
        return m

    # ── Serialization / patches ─────────────────────────────

    def serialize(
        self,
        *,
        styles_map: dict[str, Any] | None = None,
        props: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Serialize the full node (geometry + resolved style + transform)."""
        from .serializer import _dispatch_entity

        sm = styles_map if styles_map is not None else self._styles_map
        p = dict(props) if props is not None else dict(self._props)
        leaf = _dispatch_entity(self.entity, self.kind, p, sm)

        # The node's resolved style is authoritative for the style block and
        # its top-level color/opacity mirrors (frontend ``styleParam()``).
        resolved = _style_to_dict(self.style)
        if resolved:
            leaf["style"] = resolved
            if "color" in resolved:
                leaf["color"] = resolved["color"]
            if "opacity" in resolved:
                leaf["opacity"] = resolved["opacity"]

        result: dict[str, Any] = {
            "id": self.id,
            "layer": "scene",
            "kind": self.kind,
            "parent_id": self.parent.id if self.parent is not None else None,
            "transform": self.transform.to_dict(),
            "visible": self.visible,
        }
        result.update(leaf)
        return result

    def patch(self, aspect: str) -> dict[str, Any]:
        """Return an aspect-scoped patch dict for this node."""
        if aspect == "full":
            return {"id": self.id, "aspect": "full", "value": self.serialize()}
        if aspect == "style":
            return {
                "id": self.id,
                "aspect": "style",
                "value": {"style": _style_to_dict(self.style)},
            }
        if aspect == "transform":
            return {
                "id": self.id,
                "aspect": "transform",
                "value": self.transform.to_dict(),
            }
        raise ValueError(f"Unsupported aspect {aspect!r} for scene node {self.kind}")

    # ── Entity / style setters (aspect-correct) ─────────────

    def set_entity(self, entity: Any) -> None:
        """Replace the geometry entity (marks ``full``)."""
        self.entity = entity
        self.kind = type(entity).__name__
        self.mark("full")

    def set_style(self, style: Any) -> None:
        """Merge non-``None`` style fields (marks ``style``)."""
        self.style = _merge_style_into(self.style, style)
        self.mark("style")

    def set_color(self, color: Any) -> None:
        """Set the resolved style color (marks ``style``)."""
        self.style = _assign_style_field(self.style, "color", color)
        self.mark("style")

    def set_opacity(self, opacity: float) -> None:
        """Set the resolved style opacity (marks ``style``)."""
        self.style = _assign_style_field(self.style, "opacity", opacity)
        self.mark("style")

    def set_texture_label(self, texture_label: Any) -> None:
        """Set/merge the resolved style texture label (marks ``style``)."""
        if self.style is not None and hasattr(self.style, "texture_label"):
            self.style = _assign_style_field(self.style, "texture_label", texture_label)
        elif isinstance(self.style, dict):
            self.style = _assign_style_field(self.style, "texture_label", texture_label)
        self.mark("style")

    def apply_props(self, props: dict[str, Any]) -> None:
        """Merge per-entity rendering props into resolved style + stored props.

        Keeps the node's ``style`` (used for ``style`` patches) and ``_props``
        (used for full re-serialization) in sync, then marks ``style``.
        """
        if not props:
            return
        self._props.update(props)
        style = props.get("style")
        if style is not None:
            self.style = _merge_style_into(self.style, _style_to_dict(style))
        for key in ("color", "opacity"):
            if key in props:
                self.style = _assign_style_field(self.style, key, props[key])
        extra = {
            k: v for k, v in props.items() if k not in ("style", "color", "opacity")
        }
        if extra:
            self.style = _merge_style_into(self.style, extra)
        self.mark("style")

    # ── Transform mutators (aspect-correct) ─────────────────

    def set_transform(
        self,
        position: Any = None,
        rotation: Any = None,
        scale: Any = None,
    ) -> None:
        """Set transform components (marks ``transform``)."""
        self.transform.set(position=position, rotation=rotation, scale=scale)
        self.mark("transform")

    def translate(self, x: Any = 0.0, y: float = 0.0, z: float = 0.0) -> None:
        """Translate the node (marks ``transform``)."""
        self.transform.translate(x, y, z)
        self.mark("transform")

    def rotate(self, axis: Any, angle: float) -> None:
        """Rotate the node (marks ``transform``)."""
        self.transform.rotate(axis, angle)
        self.mark("transform")

    def scale_by(
        self,
        x: float = 1.0,
        y: float | None = None,
        z: float | None = None,
    ) -> None:
        """Scale the node (marks ``transform``)."""
        self.transform.scale_by(x, y, z)
        self.mark("transform")


class VizOverlayObject(VizNode):
    """Overlay-layer node (label/annotation/title): position + attach_to."""

    def __init__(
        self,
        id: str,
        *,
        kind: str = "label",
        name: str = "",
        style: Any = None,
        position: Any = (0.0, 0.0, 0.0),
        attach_to: str | None = None,
        payload: Any = None,
        visible: bool = True,
    ) -> None:
        super().__init__(id, name=name, layer="overlay", kind=kind, visible=visible)
        self.position: tuple[float, float, float] = _as_vec3(position)
        self.attach_to: str | None = attach_to
        self.style: Any = style
        self.payload: Any = payload

    def set_payload(self, payload: Any) -> None:
        """Set the kind-specific payload (marks ``full``)."""
        self.payload = payload
        self.mark("full")

    def set_position(self, position: Any) -> None:
        """Set the anchor position (marks ``full``)."""
        self.position = _as_vec3(position)
        self.mark("full")

    def set_style(self, style: Any) -> None:
        """Merge non-``None`` style fields (marks ``style``)."""
        self.style = _merge_style_into(self.style, style)
        self.mark("style")

    # ── Serialization / patches ─────────────────────────────

    def serialize(self) -> dict[str, Any]:
        """Serialize the full overlay node (position/attach_to + payload + style)."""
        result: dict[str, Any] = {
            "id": self.id,
            "layer": "overlay",
            "kind": self.kind,
            "visible": self.visible,
        }
        if self.kind == "label":
            result["position"] = list(self.position)
            result["attach_to"] = self.attach_to
            result["text"] = self.payload
        elif self.kind == "annotation":
            result["positioning"] = "fixed"
            result["anchor"] = "bottom"
            result["text"] = self.payload
        elif self.kind == "title":
            result["positioning"] = "fixed"
            result["anchor"] = "top"
            result["text"] = self.payload
        else:
            result["position"] = list(self.position)
            if self.attach_to is not None:
                result["attach_to"] = self.attach_to
            if self.payload is not None:
                result["text"] = self.payload

        style = _style_to_dict(self.style)
        if self.kind == "label":
            style.pop("offset_local", None)
        result["style"] = style
        return result

    def patch(self, aspect: str) -> dict[str, Any]:
        """Return an aspect-scoped patch dict for this overlay node."""
        if aspect == "full":
            return {"id": self.id, "aspect": "full", "value": self.serialize()}
        if aspect == "style":
            return {
                "id": self.id,
                "aspect": "style",
                "value": {"style": _style_to_dict(self.style)},
            }
        raise ValueError(f"Unsupported aspect {aspect!r} for overlay node {self.kind}")


class VizGroup(VizSceneObject):
    """A container node with no entity/style, ``kind == "VizGroup"``."""

    def __init__(
        self,
        id: str,
        *,
        name: str = "",
        transform: Transform | None = None,
        visible: bool = True,
    ) -> None:
        super().__init__(
            id,
            None,
            None,
            name=name,
            kind="VizGroup",
            transform=transform,
            visible=visible,
        )

    def serialize(
        self,
        *,
        styles_map: dict[str, Any] | None = None,
        props: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Serialize a group node (no entity/style, only transform + parenting)."""
        return {
            "id": self.id,
            "layer": "scene",
            "kind": "VizGroup",
            "parent_id": self.parent.id if self.parent is not None else None,
            "transform": self.transform.to_dict(),
            "visible": self.visible,
        }