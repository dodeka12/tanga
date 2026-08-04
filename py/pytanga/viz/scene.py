# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Scene configuration and state management for the Tanga 3D viewer.

Provides CameraConfig and SceneConfig dataclasses (sent to the browser on
initial WebSocket handshake), plus a Scene class that tracks objects
(entities, labels, overlays) in a unified ``SceneObject`` registry,
generates unique IDs, and computes dirty/removal diffs for efficient updates.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal
from uuid import uuid4

from pytanga.geometry.entities import Entity as GeoEntity

# ── Configuration ──────────────────────────────────────────


@dataclass
class CameraConfig:
    """Camera configuration for the 3D viewer.

    All fields are optional. When a field is None, the browser uses its
    default or computes the value automatically from scene bounds (auto-fit).
    """

    position: tuple[float, float, float] | None = None  # (x, y, z)
    target: tuple[float, float, float] | None = None  # look-at point
    fov: float | None = None  # vertical field of view in degrees
    near: float | None = None  # near clipping plane
    far: float | None = None  # far clipping plane

    def to_dict(self) -> dict:
        """Serialize to a JSON-compatible dict, omitting None values."""
        result: dict[str, Any] = {}
        if self.position is not None:
            result["position"] = list(self.position)
        if self.target is not None:
            result["target"] = list(self.target)
        if self.fov is not None:
            result["fov"] = self.fov
        if self.near is not None:
            result["near"] = self.near
        if self.far is not None:
            result["far"] = self.far
        return result


@dataclass
class SceneConfig:
    """Configuration for the 3D viewer scene.

    Sent to the browser on initial WebSocket handshake as a ``scene_config``
    message, before any entity data.
    """

    space_extent: float = 10.0  # half-extent of visible space; affects grid size
    show_grid: bool = True  # show ground grid
    show_axes: bool = True  # show RGB axes helper
    background_color: str = "#1a1a2e"
    camera: CameraConfig | None = None  # None = auto-fit from entities
    title: str = "Tanga 3D Viewer"  # viewport title overlay
    annotation: str | None = None  # markdown annotation text
    name: str = ""  # scene name (empty string = main scene)
    space_dim: int = 3  # 2 or 3 — controls camera mode, controls, and rendering

    def to_dict(self) -> dict:
        """Serialize to a JSON-compatible dict."""
        result: dict[str, Any] = {
            "type": "scene_config",
            "space_extent": self.space_extent,
            "show_grid": self.show_grid,
            "show_axes": self.show_axes,
            "background_color": self.background_color,
            "title": self.title,
            "name": self.name,
            "space_dim": self.space_dim,
        }
        if self.camera is not None:
            cam = self.camera.to_dict()
            if cam:
                result["camera"] = cam
        if self.annotation is not None:
            result["annotation"] = self.annotation
        return result


# ── Scene Object ────────────────────────────────────────────


@dataclass
class SceneObject:
    """A drawable element in the 3D scene or overlay layer.

    Replaces the old ``SceneEntity`` / label split.  Every piece of content
    — geometric entity, operator, label, slider, button — is a ``SceneObject``
    with a ``layer`` that tells the frontend how to render it.
    """

    id: str  # unique ID (UUID8)
    layer: Literal["scene", "overlay"] = "scene"
    kind: str = ""  # "Point", "Sphere", "label", "slider", "button", ...
    data: Any = None  # GeoEntity, Label, dict, ...
    properties: dict[str, Any] = field(default_factory=dict)
    dirty: bool = True


# ── Scene State Manager ────────────────────────────────────


class Scene:
    """Manages the state of all drawable objects and scene configuration.

    Uses a single ``_objects`` dict — no separate entity / label / control
    storage.  The ``layer`` field routes each object to the correct renderer
    on the frontend.
    """

    def __init__(self, config: SceneConfig | None = None, *, name: str = "") -> None:
        self.config = config or SceneConfig()
        self.config.name = name
        self.name: str = name
        self._objects: dict[str, SceneObject] = {}
        self._order: list[str] = []
        self._removed_ids: list[str] = []
        self._controls: dict[str, Any] = {}
        self._groups: dict[str, Any] = {}

    # -- Object lifecycle -------------------------------------

    def add_object(
        self,
        obj: SceneObject,
        *,
        object_id: str | None = None,
    ) -> str:
        """Add a SceneObject and return its ID."""
        oid = object_id or _generate_id()
        obj.id = oid
        self._objects[oid] = obj
        self._order.append(oid)
        return oid

    def _get(self, object_id: str) -> SceneObject:
        ent = self._objects.get(object_id)
        if ent is None:
            raise KeyError(f"Object {object_id!r} not found")
        return ent

    # -- Backward-compat helper for Visualizer.add() ---------

    def add(
        self,
        entity: GeoEntity | None,
        *,
        entity_id: str | None = None,
        **properties: Any,
    ) -> str:
        """Add a scene-layer entity (backward-compat wrapper for ``add_object``)."""
        eid = entity_id or _generate_id()
        resolved_kind = type(entity).__name__ if entity else "Unknown"
        obj = SceneObject(
            id=eid,
            layer="scene",
            kind=resolved_kind,
            data=entity,
            properties=dict(properties),
            dirty=True,
        )
        return self.add_object(obj, object_id=eid)

    def add_label(self, label: Any, *, label_id: str | None = None) -> str:
        """Add a label as an overlay object (backward-compat wrapper)."""
        lid = label_id or _generate_id()
        obj = SceneObject(
            id=lid,
            layer="overlay",
            kind="label",
            data=label,
            properties={},
            dirty=True,
        )
        return self.add_object(obj, object_id=lid)

    def update(self, object_id: str, **properties: Any) -> None:
        """Update rendering properties of an existing object."""
        obj = self._get(object_id)
        obj.properties.update(properties)
        obj.dirty = True

    def update_label(
        self,
        object_id: str,
        *,
        text: str | None = None,
        style: Any | None = None,
    ) -> None:
        """Update a label's text and/or style without changing its position.

        Args:
            object_id: The label's scene object ID (returned by ``add()``
                when passing a ``Label``, or retrievable via scene introspection).
            text: New label text.  ``None`` leaves unchanged.
            style: New ``LabelStyle`` instance.  ``None`` leaves unchanged.
        """
        obj = self._get(object_id)
        if text is not None:
            obj.data.text = text
        if style is not None:
            if obj.data.style is None:
                obj.data.style = style
            else:
                for field_name, value in style.__dict__.items():
                    if value is not None:
                        setattr(obj.data.style, field_name, value)
            # If offset_local changed, recompute the label position
            if style.offset_local is not None and obj.data.parent_id is not None:
                parent_obj = self._objects.get(obj.data.parent_id)
                if parent_obj is not None and parent_obj.layer == "scene":
                    from ._label_frame import compute_label_position

                    obj.data.position = compute_label_position(
                        parent_obj.data, style.offset_local
                    )
        obj.dirty = True

    def update_entity(self, entity_id: str, entity: GeoEntity) -> None:
        """Replace the geometry entity for an existing scene-layer ID."""
        obj = self._get(entity_id)
        obj.data = entity
        obj.kind = type(entity).__name__
        obj.dirty = True

    def remove(self, object_id: str) -> None:
        """Mark an object for removal in the next flush."""
        if object_id in self._objects:
            self._removed_ids.append(object_id)

    def clear(self) -> None:
        """Remove all objects."""
        for oid in list(self._objects):
            self._removed_ids.append(oid)

    # -- Sync / flush ----------------------------------------

    def flush(
        self,
        *,
        styles_map: dict[str, Any] | None = None,
    ) -> tuple[list[dict[str, Any]], list[str]]:
        """Return (dirty_object_dicts, removed_ids) and reset tracking.

        ``styles_map`` is the Visualizer's per-kind style dict.
        """
        dirty: list[dict[str, Any]] = []
        removed = list(self._removed_ids)

        for oid in list(self._removed_ids):
            self._objects.pop(oid, None)
            try:
                self._order.remove(oid)
            except ValueError:
                pass
        self._removed_ids.clear()

        for oid in self._order:
            obj = self._objects.get(oid)
            if obj is None:
                continue
            if obj.dirty:
                dirty.append(_serialize_object(obj, styles_map=styles_map))
                obj.dirty = False

        return dirty, removed

    def full_state(
        self,
        *,
        styles_map: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Return all objects serialized (for initial client sync)."""
        result: list[dict[str, Any]] = []
        for oid in self._order:
            obj = self._objects.get(oid)
            if obj is not None:
                result.append(_serialize_object(obj, styles_map=styles_map))
        return result

    # -- Backward-compat helpers (used by visualizer.py) ----

    def _serialize_labels(self) -> list[dict[str, Any]]:
        """Return all labels serialized (for export, backward compat)."""
        from .serializer import _serialize_label

        result: list[dict[str, Any]] = []
        for oid in self._order:
            obj = self._objects.get(oid)
            if obj is not None and obj.layer == "overlay" and obj.kind == "label":
                result.append(_serialize_label(obj.data, oid))
        return result

    # -- Helpers -----------------------------------------------

    @property
    def entity_count(self) -> int:
        """Number of live objects."""
        return len(self._objects)

    # -- Control storage ---------------------------------------

    def add_control(self, ctrl: Any) -> None:
        """Register a control on the scene (stored separately from scene objects)."""
        self._controls[ctrl.id] = ctrl

    def add_group(self, group: Any) -> None:
        """Register a control group on the scene."""
        self._groups[group.id] = group

    def remove_control(self, cid: str) -> None:
        """Remove a control by ID."""
        self._controls.pop(cid, None)

    def remove_group(self, gid: str) -> None:
        """Remove a control group by ID."""
        self._groups.pop(gid, None)

    def clear_controls(self) -> None:
        """Remove all controls and groups."""
        self._controls.clear()
        self._groups.clear()


def _generate_id() -> str:
    return uuid4().hex[:8]


# ── Serialization helper ──────────────────────────────────


def _serialize_object(
    obj: SceneObject,
    *,
    styles_map: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Serialize a SceneObject to a JSON-ready dict.

    Dispatches on ``obj.layer`` to the appropriate serializer.
    """
    from .serializer import _serialize_label, serialize_entity

    if obj.layer == "overlay":
        if obj.kind == "label":
            return _serialize_label(obj.data, obj.id)
        if obj.kind == "annotation":
            return _serialize_annotation(obj)
        if obj.kind == "title":
            return _serialize_title(obj)
        # Generic overlay (future: sliders, buttons, etc.)
        return {
            "id": obj.id,
            "layer": "overlay",
            "kind": obj.kind,
        }

    # scene layer: serialize as entity
    return serialize_entity(
        obj.data,
        obj.id,
        obj.properties,
        kind=obj.kind,
        styles_map=styles_map,
    )


def _serialize_annotation(obj: SceneObject) -> dict[str, Any]:
    """Serialize an annotation overlay object."""
    text = obj.data.get("text", "") if isinstance(obj.data, dict) else ""
    style = obj.data.get("style", {}) if isinstance(obj.data, dict) else {}
    return {
        "id": obj.id,
        "layer": "overlay",
        "kind": "annotation",
        "positioning": "fixed",
        "anchor": "bottom",
        "text": text,
        "style": style,
    }


def _serialize_title(obj: SceneObject) -> dict[str, Any]:
    """Serialize a title overlay object."""
    text = obj.data.get("text", "") if isinstance(obj.data, dict) else ""
    style = obj.data.get("style", {}) if isinstance(obj.data, dict) else {}
    return {
        "id": obj.id,
        "layer": "overlay",
        "kind": "title",
        "positioning": "fixed",
        "anchor": "top",
        "text": text,
        "style": style,
    }
