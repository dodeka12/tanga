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
from typing import TYPE_CHECKING, Any, Literal
from uuid import uuid4

from pytanga.geometry.entities import Entity as GeoEntity

from .camera import CameraConfig
from ._nodes import VizGroup, VizNode, VizOverlayObject, VizSceneObject
from ._types import SceneEntity, TransformRotation, Triple, Vec3, VizInputType
from ._props import _normalize_color
from ._style_dict import _resolve_label_style, _resolve_tex_label_style
from ._viz_styles import VizStyles, make_styles

if TYPE_CHECKING:
    from ._styles import LabelStyle, ObjVizStyle, TextureLabelStyle

# ── Configuration ──────────────────────────────────────────


@dataclass
class SceneConfig:
    """Configuration for the 3D viewer scene.

    Sent to the browser on initial WebSocket handshake as a ``scene_config``
    message, before any entity data.
    """

    background_color: str | None = None
    camera: CameraConfig | None = None  # None = auto-fit from entities
    title: str = "Tanga 3D Viewer"  # viewport title overlay
    annotation: str | None = None  # markdown annotation text
    name: str = ""  # scene name (empty string = main scene)
    space_dim: int = 3  # 2 or 3 — controls camera mode, controls, and rendering

    def to_dict(self) -> dict:
        """Serialize to a JSON-compatible dict."""
        result: dict[str, Any] = {
            "type": "scene_config",
            "title": self.title,
            "name": self.name,
            "scene": self.name,
            "space_dim": self.space_dim,
        }
        if self.background_color is not None:
            # Omitted (not ``None``) means "follow the active theme's
            # ``--tanga-bg`` token" on the frontend.
            result["background_color"] = self.background_color
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

    def __init__(
        self,
        config: SceneConfig | None = None,
        *,
        name: str = "",
        styles: VizStyles | None = None,
        host: Any = None,
    ) -> None:
        self.config = config or SceneConfig()
        self.config.name = name
        self.name: str = name
        self.styles: VizStyles = styles or make_styles()
        self._host = host
        self._objects: dict[str, SceneObject] = {}
        self._nodes: dict[str, VizNode] = {}
        self._order: list[str] = []
        self._removed_ids: list[str] = []
        self._controls: dict[str, Any] = {}
        self._groups: dict[str, Any] = {}
        self._interaction_configs: dict[str, Any] = {}

    # -- Object lifecycle -------------------------------------

    def add_object(
        self,
        obj: SceneObject,
        *,
        object_id: str | None = None,
    ) -> str:
        """Add a SceneObject and return its ID.

        Also builds and stores the corresponding scene-graph node (with a
        resolved style) in ``_nodes``.
        """
        oid = object_id or _generate_id()
        obj.id = oid
        self._objects[oid] = obj
        self._order.append(oid)
        self._nodes[oid] = self._make_node(obj)
        return oid

    # -- Node construction / accessors -----------------------

    def _make_node(self, obj: SceneObject) -> VizNode:
        """Build the scene-graph node for *obj*, resolving its style."""
        if obj.layer == "overlay":
            return self._make_overlay_node(obj)
        return self._make_scene_node(obj)

    def _make_scene_node(self, obj: SceneObject) -> VizSceneObject:
        """Build a scene-layer node with a resolved style (canonical + user)."""
        from ._styles import _style_to_output

        props = obj.properties or {}
        kind = obj.kind
        merged = _style_to_output(props.get("style"), kind, styles_map=self.styles.kind)
        if props.get("color") is not None:
            merged["color"] = props["color"]
        if props.get("opacity") is not None:
            merged["opacity"] = props["opacity"]
        node = VizSceneObject(
            obj.id,
            obj.data,
            merged,
            name=obj.kind,
            kind=kind,
            props=props,
            styles_map=self.styles.kind,
        )
        # An SdfGroup mutated directly through `ref.entity.set_member_transform()`
        # must mark its node's content dirty; wire a change hook for that.
        from .sdf.group import SdfGroup

        if isinstance(node.entity, SdfGroup):
            node.entity.on_change = lambda: node.mark("content")
        return node

    def _make_overlay_node(self, obj: SceneObject) -> VizOverlayObject:
        """Build an overlay-layer node from a label/annotation/title object."""
        if obj.kind == "label":
            label = obj.data
            return VizOverlayObject(
                obj.id,
                kind="label",
                style=getattr(label, "style", None) or self.styles.label_base,
                position=getattr(label, "position", (0.0, 0.0, 0.0)),
                attach_to=getattr(label, "parent_id", None),
                payload=getattr(label, "text", None),
            )
        data = obj.data if isinstance(obj.data, dict) else {}
        return VizOverlayObject(
            obj.id,
            kind=obj.kind,
            style=data.get("style", {}),
            payload=data.get("text", ""),
        )

    def get_node(self, object_id: str) -> VizNode:
        """Return the scene-graph node for *object_id*."""
        node = self._nodes.get(object_id)
        if node is None:
            raise KeyError(f"Object {object_id!r} not found")
        return node

    def add_node(self, node: VizNode, *, object_id: str | None = None) -> str:
        """Register a scene-graph node and return its ID."""
        oid = object_id or node.id or _generate_id()
        node.id = oid
        self._nodes[oid] = node
        if oid not in self._order:
            self._order.append(oid)
        return oid

    def add_group(self, name: str | None = None) -> VizGroup:
        """Create and register a scene-graph group (``kind == "VizGroup"``)."""
        gid = _generate_id()
        group = VizGroup(gid, name=name or "")
        self._nodes[gid] = group
        self._order.append(gid)
        return group

    @property
    def group_ids(self) -> list[str]:
        """IDs of all scene-graph groups."""
        return [oid for oid, node in self._nodes.items() if node.kind == "VizGroup"]

    def _dfs_preorder(self) -> list[VizNode]:
        """Return all nodes in DFS pre-order (parents before children)."""
        result: list[VizNode] = []
        visited: set[str] = set()

        def visit(node: VizSceneObject) -> None:
            if node.id in visited:
                return
            visited.add(node.id)
            result.append(node)
            for child in node.children:
                visit(child)

        for oid in self._order:
            node = self._nodes.get(oid)
            if node is None:
                continue
            if isinstance(node, VizSceneObject) and node.parent is None:
                visit(node)
            elif node.id not in visited:
                visited.add(node.id)
                result.append(node)
        return result

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


    # ── High-level entity facade (moved from Visualizer) ────
    def add_viz(
        self,
        obj: VizInputType | None = None,
        *,
        entity_id: str | None = None,
        color: Any = None,
        opacity: float | None = None,
        style: ObjVizStyle | None = None,
        label: str | None = None,
        label_style: LabelStyle | None = None,
        tex_label: str | None = None,
        tex_label_style: "TextureLabelStyle | None" = None,
        parent_id: str | None = None,
        attach_to: str | None = None,
    ) -> str:
        """Add an entity to this scene.

        ``parent_id`` parents the new scene node under an existing scene node;
        ``attach_to`` sets the scene-node reference for a label created here.
        """
        from ._active import ActSceneObject
        from ._label import Label
        from ._nodes import VizGroup, VizSceneObject
        from ._scene_handle import VizSceneHandle
        from ._styles import TextureLabelStyle as _TLS

        if isinstance(obj, VizGroup):
            from .scene import _generate_id

            gid = entity_id or obj.id or _generate_id()
            obj.id = gid
            self.add_node(obj, object_id=gid)
            if parent_id is not None:
                parent = self.get_node(parent_id)
                if isinstance(parent, VizSceneObject):
                    parent.add_child(obj)
            return gid

        if isinstance(obj, ActSceneObject):
            properties: dict[str, Any] = {}
            if color is not None:
                normalized = _normalize_color(color)
                if isinstance(normalized, tuple):
                    properties["color"] = normalized[0]
                    if opacity is None:
                        properties["opacity"] = normalized[1]
                else:
                    properties["color"] = normalized
            if opacity is not None:
                properties["opacity"] = float(opacity)
            if style is not None:
                properties["style"] = style
            eid = self.add(obj.entity, entity_id=entity_id, **properties)
            obj._init(VizSceneHandle(self._host, self.name), eid)
            self._host._act_objects[eid] = obj
            self._attach_to_parent(eid, parent_id)
            self._add_label_for_entity(
                obj.entity,
                eid,
                label=label,
                label_style=label_style,
                attach_to=attach_to,
                properties=properties,
            )
            return eid

        if isinstance(obj, Label):
            if attach_to is not None:
                obj.parent_id = attach_to
            return self.add_label(obj)

        properties: dict[str, Any] = {}

        if color is not None:
            normalized = _normalize_color(color)
            if isinstance(normalized, tuple):
                properties["color"] = normalized[0]
                if opacity is None:
                    properties["opacity"] = normalized[1]
            else:
                properties["color"] = normalized

        if opacity is not None:
            properties["opacity"] = float(opacity)

        # Build texture label convenience style if tex_label is set
        _tex_label_merged: _TLS | None = None
        if tex_label is not None:
            entity_for_kind = _resolve_scene_entity(obj)
            kind = type(entity_for_kind).__name__
            _tex_label_merged = _resolve_tex_label_style(
                self.styles.tex_label_base,
                self.styles.tex_label_kind.get(kind),
                tex_label_style,
            )
            _tex_label_merged.text = tex_label

        # Merge texture label into style if the user didn't provide
        # texture_label explicitly via style
        if _tex_label_merged is not None:
            if style is not None:
                from ._styles import PlaneStyle, SphereStyle

                style_for_check = style
                if isinstance(style_for_check, (SphereStyle, PlaneStyle)):
                    if style_for_check.texture_label is None:
                        style_for_check.texture_label = _tex_label_merged
                # Otherwise leave the user's explicit style alone
            else:
                kind_for_style = None
                entity_for_style = _resolve_scene_entity(obj)
                if entity_for_style is not None:
                    kind_for_style = type(entity_for_style).__name__
                if kind_for_style == "Sphere":
                    from ._styles import SphereStyle as SS

                    style = SS(
                        texture_label=_tex_label_merged,
                        wireframe=False,
                        # double_sided=True,
                    )
                elif kind_for_style == "Plane":
                    from ._styles import PlaneStyle as PS

                    style = PS(texture_label=_tex_label_merged, wireframe=False)

        if style is not None:
            properties["style"] = style

        entity = _resolve_scene_entity(obj)

        # Viz-level drawables (PointPath, etc.) go through add_object
        from pytanga.geometry.entities import Entity as GeoEntity
        from pytanga.geometry.operators import Operator as GeoOperator

        if not isinstance(entity, (GeoEntity, GeoOperator)):
            kind = type(entity).__name__
            oid = self.add_object(
                SceneObject(
                    id=entity_id or "",
                    layer="scene",
                    kind=kind,
                    data=entity,
                    properties=properties,
                    dirty=True,
                ),
                object_id=entity_id,
            )
            self._attach_to_parent(oid, parent_id)
            self._add_label_for_entity(
                entity,
                oid,
                label=label,
                label_style=label_style,
                attach_to=attach_to,
                properties=properties,
            )
            return oid

        eid = self.add(entity, entity_id=entity_id, **properties)
        self._attach_to_parent(eid, parent_id)

        self._add_label_for_entity(
            entity,
            eid,
            label=label,
            label_style=label_style,
            attach_to=attach_to,
            properties=properties,
        )
        return eid

    def _attach_to_parent(self, oid: str, parent_id: str | None) -> None:
        """Attach a scene node to a parent scene node (no-op when ``parent_id`` is ``None``)."""
        if parent_id is None:
            return
        from ._nodes import VizSceneObject

        child = self.get_node(oid)
        parent = self.get_node(parent_id)
        if isinstance(child, VizSceneObject) and isinstance(parent, VizSceneObject):
            parent.add_child(child)

    def _add_label_for_entity(
        self,
        entity: Any,
        eid: str,
        *,
        label: str | None,
        label_style: LabelStyle | None,
        attach_to: str | None,
        properties: dict[str, Any],
    ) -> None:
        """Create a label for *entity* attached to *eid*.

        No-op when *label* is ``None``.  Shared by the regular entity path and
        the :class:`ActSceneObject` path so active objects support ``label=``.
        """
        if label is None:
            return
        from ._label import Label
        from ._label_frame import compute_label_position
        from .serializer import resolve_line_length

        from pytanga.geometry.entities import Line
        from pytanga.geometry.operators import ReflectionLine

        kind = type(entity).__name__
        resolved_ls = _resolve_label_style(
            self.styles.label_base,
            self.styles.label_kind.get(kind),
            label_style,
        )

        line_length = None
        if isinstance(entity, Line):
            line_length = resolve_line_length(
                entity, styles_map=self.styles.kind, props=properties
            )
        elif isinstance(entity, ReflectionLine):
            line_length = resolve_line_length(
                entity.line, styles_map=self.styles.kind, props=properties
            )

        position = compute_label_position(
            entity,
            resolved_ls.offset_local,
            along=resolved_ls.along,
            line_length=line_length,
        )
        lbl = Label(
            text=label,
            position=position,
            parent_id=attach_to if attach_to is not None else eid,
            style=resolved_ls,
        )
        self.add_label(lbl)

    def update(self, object_id: str, **properties: Any) -> None:
        """Update rendering properties of an existing object."""
        obj = self._get(object_id)
        obj.properties.update(properties)
        obj.dirty = True

        node = self._nodes.get(object_id)
        if isinstance(node, VizSceneObject):
            node.apply_props(dict(properties))

    def update_label(
        self,
        object_id: str,
        *,
        text: str | None = None,
        style: Any | None = None,
    ) -> None:
        """Update a label's text and/or style (and position when the anchor changes)."""
        obj = self._get(object_id)
        node = self._nodes.get(object_id)

        if text is not None:
            obj.data.text = text

        new_position: tuple[float, float, float] | None = None
        if style is not None:
            if obj.data.style is None:
                obj.data.style = style
            else:
                for field_name, value in style.__dict__.items():
                    if value is not None:
                        setattr(obj.data.style, field_name, value)
            # If the anchor offset or the along parameter changed, recompute
            # the label position.
            if (
                style.offset_local is not None or style.along is not None
            ) and obj.data.parent_id is not None:
                parent_obj = self._objects.get(obj.data.parent_id)
                if parent_obj is not None and parent_obj.layer == "scene":
                    from ._label_frame import compute_label_position
                    from .serializer import resolve_line_length

                    from pytanga.geometry.entities import Line
                    from pytanga.geometry.operators import ReflectionLine

                    merged = obj.data.style
                    parent_entity = parent_obj.data
                    line_length = None
                    if isinstance(parent_entity, Line):
                        line_length = resolve_line_length(
                            parent_entity, styles_map=self.styles.kind
                        )
                    elif isinstance(parent_entity, ReflectionLine):
                        line_length = resolve_line_length(
                            parent_entity.line, styles_map=self.styles.kind
                        )

                    new_position = compute_label_position(
                        parent_entity,
                        merged.offset_local,
                        along=merged.along,
                        line_length=line_length,
                    )

        if new_position is not None:
            obj.data.position = new_position
        obj.dirty = True

        if isinstance(node, VizOverlayObject):
            if text is not None:
                node.set_payload(text)
            if style is not None:
                node.set_style(style)
            if new_position is not None:
                node.set_position(new_position)

    def update_entity(self, entity_id: str, entity: GeoEntity) -> None:
        """Replace the geometry entity for an existing scene-layer ID."""
        obj = self._get(entity_id)
        obj.data = entity
        obj.kind = type(entity).__name__
        obj.dirty = True

        node = self._nodes.get(entity_id)
        if isinstance(node, VizSceneObject):
            node.set_entity(entity)

    def update_sdf_group_member(
        self,
        object_id: str,
        member: int | str,
        *,
        position: Vec3 = None,
        rotation: TransformRotation = None,
        scale: Triple = None,
    ) -> None:
        """Update an ``SdfGroup`` member's runtime transform.

        *member* is either the member's 0-based index or its ``id``. Marks the
        node's ``content`` aspect dirty so the next flush pushes the updated
        member transform (the frontend updates the member uniform and resizes
        the proxy box in place).
        """
        from .sdf.group import SdfGroup

        node = self._nodes.get(object_id)
        if node is None:
            raise KeyError(f"Object {object_id!r} not found")
        if not isinstance(node, VizSceneObject):
            raise TypeError(f"Object {object_id!r} is not a scene object")
        group = node.entity
        if not isinstance(group, SdfGroup):
            raise TypeError(f"Object {object_id!r} is not an SdfGroup")
        group.set_member_transform(
            member, position=position, rotation=rotation, scale=scale
        )
        node.mark("content")

    def remove(self, object_id: str) -> None:
        """Mark an object (or group node) for removal in the next flush.

        Removing a group node also removes its whole descendant subtree.
        Labels attached (via ``parent_id``) to the removed object or any of
        its descendants are removed too.
        """
        removed_ids: set[str] = set()
        if object_id in self._objects or object_id in self._nodes:
            self._removed_ids.append(object_id)
            removed_ids.add(object_id)
        node = self._nodes.get(object_id)
        if isinstance(node, VizSceneObject):
            for descendant in self._descendants(node):
                if descendant.id not in self._removed_ids:
                    self._removed_ids.append(descendant.id)
                removed_ids.add(descendant.id)
                self._interaction_configs.pop(descendant.id, None)
        self._interaction_configs.pop(object_id, None)

        # Remove labels attached to the removed object (or any descendant).
        for oid, obj in list(self._objects.items()):
            if obj.layer == "overlay" and obj.kind == "label":
                if getattr(obj.data, "parent_id", None) in removed_ids:
                    if oid not in self._removed_ids:
                        self._removed_ids.append(oid)

    @staticmethod
    def _descendants(node: VizSceneObject):
        """Yield *node*'s descendants in DFS pre-order (children first)."""
        for child in node.children:
            yield child
            yield from Scene._descendants(child)

    def clear(self) -> None:
        """Remove all objects and group nodes."""
        for oid in list(self._objects):
            self._removed_ids.append(oid)
        for oid in list(self._nodes):
            if oid not in self._removed_ids:
                self._removed_ids.append(oid)
        self._interaction_configs.clear()

    # -- Interaction config management -----------------------

    def set_interaction(self, object_id: str, config: Any) -> None:
        """Set or update the interaction configuration for an entity.

        The config is a :class:`~pytanga.viz._interaction.InteractionConfig`
        instance.  It is included in the entity JSON on the next flush.
        """
        self._interaction_configs[object_id] = config
        # Mark entity dirty so the interaction field is re-sent
        obj = self._objects.get(object_id)
        if obj is not None:
            obj.dirty = True
        node = self._nodes.get(object_id)
        if node is not None:
            node.mark("full")

    def get_interaction(self, object_id: str) -> Any | None:
        """Get the interaction config for an entity, or ``None``."""
        return self._interaction_configs.get(object_id)

    def remove_interaction(self, object_id: str) -> None:
        """Remove the interaction config for an entity."""
        self._interaction_configs.pop(object_id, None)

    # -- Sync / flush ----------------------------------------

    def flush(
        self,
        *,
        styles_map: dict[str, Any] | None = None,
    ) -> tuple[list[dict[str, Any]], list[str]]:
        """Return (aspect_patches, removed_ids) and reset dirty tracking.

        Walks the scene-graph nodes in DFS pre-order and collects one
        aspect-scoped patch per dirty aspect (``full`` / ``style`` /
        ``transform`` / ``content``).  Nodes use their scene-snapshotted
        styles by default.
        """
        patches: list[dict[str, Any]] = []
        removed = list(self._removed_ids)

        for oid in list(self._removed_ids):
            self._objects.pop(oid, None)
            self._nodes.pop(oid, None)
            try:
                self._order.remove(oid)
            except ValueError:
                pass
        self._removed_ids.clear()

        for node in self._dfs_preorder():
            dirty_aspects = node.consume_dirty()
            if not dirty_aspects:
                continue
            for aspect in ("full", "style", "transform", "content"):
                if aspect not in dirty_aspects:
                    continue
                patch = node.patch(aspect)
                if aspect == "full" and node.layer == "scene":
                    _inject_interaction(
                        patch["value"], node.id, self._interaction_configs
                    )
                patches.append(patch)

        return patches, removed

    def full_state(
        self,
        *,
        styles_map: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Return all nodes serialized (for initial client sync / export)."""
        result: list[dict[str, Any]] = []
        for node in self._dfs_preorder():
            if isinstance(node, VizSceneObject):
                entity_dict = node.serialize(styles_map=styles_map)
            else:
                entity_dict = node.serialize()
            if node.layer == "scene":
                _inject_interaction(entity_dict, node.id, self._interaction_configs)
            result.append(entity_dict)
        return result

    def clear_dirty(self) -> None:
        """Reset dirty tracking on all nodes.

        Called after an initial full-state sync so a subsequent :meth:`flush`
        only sends changes made after the sync — not a redundant re-send of the
        whole scene, which would otherwise force the frontend to rebuild every
        object and orphan their CSS2D labels.
        """
        for node in self._dfs_preorder():
            node.consume_dirty()

    # -- Label look-up -----------------------------------------

    def get_label_ids(self, entity_id: str) -> list[str]:
        """Return the IDs of all labels attached to *entity_id*."""
        result: list[str] = []
        for oid, obj in self._objects.items():
            if obj.layer == "overlay" and obj.kind == "label":
                if getattr(obj.data, "parent_id", None) == entity_id:
                    result.append(oid)
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

    def add_control_group(self, group: Any) -> None:
        """Register a control group (UI controls) on the scene."""
        self._groups[group.id] = group

    def remove_control(self, cid: str) -> None:
        """Remove a control by ID."""
        self._controls.pop(cid, None)

    def remove_control_group(self, gid: str) -> None:
        """Remove a control group by ID."""
        self._groups.pop(gid, None)

    def clear_controls(self) -> None:
        """Remove all controls and groups."""
        self._controls.clear()
        self._groups.clear()


def _resolve_scene_entity(obj: Any) -> SceneEntity:
    """Resolve an MV to a :class:`SceneEntity`.

    Viz-level drawables (PointPath, …) are passed through unchanged.
    GeoEntities and Operators are returned as-is.
    MVs are resolved via :func:`pytanga.geometry.analyze`, reading the
    MV's ``algebra.opns`` flag.
    """
    from pytanga.geometry.operators import Operator as GeoOperator

    if isinstance(obj, SceneEntity):
        return obj  # type: ignore[return-value]

    from .sdf._compose import SdfElement as _SdfElement
    from .sdf.primitives import SdfNode as _SdfNode

    if isinstance(obj, (_SdfElement, _SdfNode)):
        return obj  # type: ignore[return-value]

    if isinstance(obj, (GeoEntity, GeoOperator)):
        return obj  # type: ignore[return-value]

    try:
        from pytanga.geometry import analyze

        result = analyze(obj)
        if result is None:
            raise ValueError(f"Could not analyze object: {obj!r}")
        return result
    except ImportError:
        raise TypeError(
            f"Object of type {type(obj).__name__} is not a recognized "
            f"geometry entity, operator, or multivector."
        ) from None


def _generate_id() -> str:
    return uuid4().hex[:8]


def _inject_interaction(
    entity_dict: dict[str, Any],
    object_id: str,
    interaction_configs: dict[str, Any],
) -> None:
    """Inject the ``"interaction"`` field into a serialized entity dict.

    Only adds the field for scene-layer objects that have an enabled
    interaction config.  Overlay objects (labels, annotations) are
    skipped — they never have interaction configs.
    """
    ic = interaction_configs.get(object_id)
    if ic is not None and getattr(ic, "enabled", False):
        entity_dict["interaction"] = ic.to_dict()
