# Phase 8a — Unified Scene Content Architecture (Scene + Overlay Layers)

**Prerequisites:** Phase 8 (integration), Phase 4d (labels as first-class viz objects), Phase 7 (animation)

**Goal:** Replace the parallel code paths for entities/operators vs. labels with a unified two-layer architecture that treats all drawable content as "scene objects" dispatched by a `layer` field. The overlay layer supports generalised world-position tracking — any DOM element (label, slider, button, control panel) can be attached to a 3D entity and will automatically follow its projected screen position via `CSS2DRenderer`. This also lays the foundation for future interactive controls (Phase 12+).

**Status:** ❌ Not started

---

## 1. Motivation

### 1.1 Current Problem

Every content type adds a parallel code path through all layers:

| Layer | Entities/Operators | Labels (current) | Future: Sliders/Buttons |
|-------|-------------------|------------------|------------------------|
| Python `Scene` | `_entities` dict + `_order` list | `_labels` dict + `_label_order` list | Yet another dict |
| Serializer | `serialize_entity()` → per-kind dispatch | `_serialize_label()` | New function |
| WebSocket message | `msg.entities` + `msg.removed` | `msg.labels` | `msg.controls` |
| Frontend `viewer.js` | `updateEntity()` → `entityMeshes` Map | `upsertLabel()` → `labelObjects` Map | New handler |
| Export HTML | `createEntityMesh(ent)` | inline label loop | New inline loop |

Adding interactive controls (sliders, buttons, parameter panels) would require adding a **fifth parallel path** to all six layers. This is unsustainable.

### 1.2 Design Goals

1. **One code path** for all drawable content — entities, operators, labels, controls.
2. **Respect the WebGL vs. DOM divide** — 3D meshes use `WebGLRenderer`, DOM elements use `CSS2DRenderer` or plain DOM.
3. **Generalised world-position tracking** — any DOM element can be attached to a 3D object via `parentId` and will follow its projected screen position automatically.
4. **Foundation for interactive controls** — sliders, buttons, color pickers that modify entity properties and send changes back over WebSocket.
5. **Backward compatible** — existing `viz.add(entity, label="S1")` convenience syntax continues to work.

---

## 2. Architecture: Two-Layer Model

### 2.1 Layer Definitions

```
layer: "scene"                    layer: "overlay"
─────────────────                ──────────────────────────
THREE.Mesh / THREE.Group         DOM elements (HTML)
rendered by WebGLRenderer        positioning: "world" | "fixed"

  Sphere                         │  positioning: "world"
  Line                           │    parentId: "sphere_a"
  Plane                          │    offset: [0, 1.5, 0]
  Circle                         │    → CSS2DObject, tracks 3D pos
  Rotor                          │    → use cases: labels, inline
  ...                            │      controls, tooltips, property
  (all entity/operator kinds)    │      panels attached to objects
                                 │
                                 │  positioning: "fixed"
                                 │    anchor: "top-right"
                                 │    offset: [10, 10]
                                 │    → absolute DOM, no 3D tracking
                                 │    → use cases: reset buttons,
                                 │      info bar, legend, layer
                                 │      toggles, global sliders
```

### 2.2 Python-Side: Unified `SceneObject`

A single dataclass replaces `SceneEntity` and the separate label storage:

```python
# py/pytanga/viz/scene.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass
class SceneObject:
    """A drawable element in the 3D scene or overlay layer."""

    id: str                                    # unique ID (UUID8)
    layer: Literal["scene", "overlay"] = "scene"
    kind: str = ""                             # "Sphere", "label", "slider", "button", ...
    data: Any = None                           # GeoEntity, Label, Control, ...
    properties: dict[str, Any] = field(default_factory=dict)  # rendering attrs
    dirty: bool = True
```

The `Scene` class uses a **single ordered dict** instead of parallel dicts:

```python
class Scene:
    def __init__(self, config: SceneConfig | None = None) -> None:
        self.config = config or SceneConfig()
        self._objects: dict[str, SceneObject] = {}   # id → SceneObject
        self._order: list[str] = []                  # iteration order
        self._removed_ids: list[str] = []
        self._config_sent = False
```

### 2.3 Serializer: Unified Dispatch

A single `serialize_object(obj: SceneObject) -> dict` dispatches on `obj.layer`:

```python
def serialize_object(obj: SceneObject, *, defaults, styles_map) -> dict[str, Any]:
    """Serialize a SceneObject to a JSON-ready dict."""
    result: dict[str, Any] = {"id": obj.id, "layer": obj.layer, "kind": obj.kind}

    if obj.layer == "scene":
        # Delegate to existing serialize_entity() logic
        result.update(_serialize_scene_entity(obj.data, obj.id, obj.properties, ...))
    elif obj.layer == "overlay":
        # Dispatch on obj.kind: "label", "slider", "button", "control_group", ...
        result.update(_serialize_overlay(obj))

    return result
```

### 2.4 WebSocket Message: Unified Format

```json
{
  "type": "scene_update",
  "objects": [
    {
      "id": "a1", "layer": "scene", "kind": "Sphere",
      "center": [1, 0, 0], "radius": 1.0, "color": "#ff4444"
    },
    {
      "id": "lbl_1", "layer": "overlay", "kind": "label",
      "positioning": "world", "parentId": "a1",
      "offset": [0, 1.2, 0], "text": "S₁",
      "style": { "style_type": "LabelStyle", "font_size": 14, ... }
    },
    {
      "id": "ctrl_1", "layer": "overlay", "kind": "control_group",
      "positioning": "world", "parentId": "a1",
      "offset": [1.5, 0, 0],
      "controls": [
        {"kind": "slider", "param": "opacity", "min": 0, "max": 1, "value": 0.8},
        {"kind": "color_picker", "param": "color", "value": "#ff4444"}
      ]
    },
    {
      "id": "reset_btn", "layer": "overlay", "kind": "button",
      "positioning": "fixed", "anchor": "top-right",
      "offset": [10, 10], "text": "Reset", "action": "reset_all"
    }
  ],
  "removed": []
}
```

Key points:
- `layer` discriminates WebGL scene vs. DOM overlay
- `positioning` discriminates world-tracked (CSS2DObject) vs. fixed (plain DOM)
- `parentId` references another object's ID for world-position tracking
- `kind` is now a general content-type discriminator, not just an entity type

### 2.5 Frontend: Unified `upsertObject()`

```javascript
// viewer.js refactored

const sceneObjects = new Map();    // id → {obj: THREE.Object3D | CSS2DObject | HTMLElement, layer, ...}

function handleMessage(msg) {
    if (msg.type === 'scene_update') {
        if (msg.removed) { /* ... */ }
        if (msg.objects) {
            for (const obj of msg.objects) {
                upsertObject(obj);
            }
        }
    }
    // ... animate, timeline unchanged
}

function upsertObject(msg) {
    // Remove previous instance if exists
    const old = sceneObjects.get(msg.id);
    if (old) {
        if (old.obj instanceof THREE.Object3D) old.obj.removeFromParent();
        if (old.el) old.el.remove();
        sceneObjects.delete(msg.id);
    }

    if (msg.layer === 'scene') {
        const mesh = createEntityMesh(msg);   // existing factory.js logic
        if (mesh) {
            scene.add(mesh);
            sceneObjects.set(msg.id, {obj: mesh, layer: 'scene'});
        }
    } else if (msg.layer === 'overlay') {
        const el = buildOverlayElement(msg);  // dispatches on msg.kind
        let css2d = null;

        if (msg.positioning === 'world') {
            css2d = new CSS2DObject(el);
            css2d.position.set(...(msg.offset || [0, 0, 0]));
            const parent = msg.parentId ? sceneObjects.get(msg.parentId)?.obj : null;
            (parent || scene).add(css2d);
        } else {
            // Fixed positioning: absolute DOM
            el.style.position = 'absolute';
            applyAnchor(el, msg.anchor, msg.offset);
            document.body.appendChild(el);
        }

        sceneObjects.set(msg.id, {obj: css2d, el, layer: 'overlay', positioning: msg.positioning});
    }
}

function buildOverlayElement(msg) {
    switch (msg.kind) {
        case 'label':
            return createLabelElement(msg);
        case 'slider':
            return createSliderElement(msg);
        case 'button':
            return createButtonElement(msg);
        case 'color_picker':
            return createColorPickerElement(msg);
        case 'control_group':
            return createControlGroupElement(msg);
        default:
            console.warn(`Unknown overlay kind: ${msg.kind}`);
            return null;
    }
}
```

### 2.6 World-Position Tracking (How It Works)

`CSS2DRenderer` already projects 3D world coordinates to 2D screen positions each frame and updates the CSS `transform` of the DOM element. The generalisation is trivial:

- **Labels** → `CSS2DObject` wrapping a `<div>` with text
- **Inline controls** → `CSS2DObject` wrapping a `<div>` with `<input>`, `<button>`, etc.
- **Control panels** → `CSS2DObject` wrapping a container `<div>` with grouped controls
- **Fixed HUD** → plain DOM element (no `CSS2DObject` wrapper), absolutely positioned

All CSS2D objects follow their parent entity automatically — a control panel attached to a sphere moves with the sphere during animation.

### 2.7 Interaction Flow for Controls (Forward-Looking)

```
User drags slider                WebSocket                   Python
─────────────────               ──────────                  ──────
oninput → ws.send(              {"type": "control",         viz.on_control(lambda msg:
  {type: "control",              "id": "ctrl_1/slider_0",     entity_id = msg["parentId"]
   id: "ctrl_1/slider_0",       "param": "opacity",          if msg["param"] == "opacity":
   param: "opacity",             "value": 0.5}                  viz.update(entity_id,
   value: 0.5})                                                   ObjVizProps(opacity=0.5))
                            →                           →
```

Control IDs use a `parent_id/control_index` composite key so the Python side can identify which entity the control belongs to without additional metadata.

---

## 3. Migration from Current Code

### 3.1 What Changes

| Component | Before | After |
|-----------|--------|-------|
| `Scene` | `_entities` dict + `_labels` dict | `_objects` dict (single) |
| `Scene.add()` | `add(entity, kind, entity_id, **properties)` | `add_object(obj: SceneObject)` |
| `Scene.add_label()` | Separate method | `add_object(SceneObject(layer="overlay", kind="label", data=label))` |
| `Scene.flush()` | Returns `(entities, removed)` | Returns `(objects, removed)` |
| `Scene.full_state()` | Returns entity list only | Returns all objects (scene + overlay) |
| `serializer.py` | `serialize_entity()` | `serialize_object()` — dispatches on layer |
| `server.py` | `FlushCallback` returns `(entities, removed, labels)` → 3-tuple | Reverts to `(objects, removed)` → 2-tuple |
| `viewer.js` | `entityMeshes` Map + `labelObjects` Map | `sceneObjects` Map (single) |
| `viewer.js` | `updateEntity()` + `upsertLabel()` | `upsertObject()` (single) |
| `viewer.js` message handler | `msg.entities` + `msg.labels` | `msg.objects` (single) |
| `visualizer.py` | `add()` creates Label separately | `add()` creates SceneObject with unified flow |
| Export HTML | Separate entity + label loops | Single loop over `msg.objects` |

### 3.2 What Stays the Same

- `Visualizer.add()` Python API — still `viz.add(entity, label="S1")`
- `ObjVizProps` and style classes from Phase 4c
- Per-entity JS renderers from Phase 5
- Operator JS renderers from Phase 6
- Animation system from Phase 7 (tween engine, timeline, frame streaming)
- `Server` lifecycle (`start()`, `stop()`, `push()`, `push_raw()`)
- `SceneConfig`, `CameraConfig`
- Entity → JSON serialization logic (moved from `serialize_entity` to `_serialize_scene_entity`)

---

## 4. Files to Create / Modify

### 4.1 New Files

| File | Content |
|------|---------|
| `py/pytanga/viz/_overlay.py` | Overlay serialization helpers: `_serialize_label()`, `_serialize_control()`, `_serialize_control_group()` |
| `py/tests/viz/test_phase8a_unified.py` | Tests for unified object storage, unified message format, label-as-overlay migration |

### 4.2 Heavily Modified Files

| File | Changes |
|------|---------|
| `py/pytanga/viz/scene.py` | Replace `_entities`/`_labels` with `_objects` dict; `add_object()`, `remove_object()`; unified `flush()`/`full_state()`; remove `add_label()`/`remove_label()`/`_serialize_labels()` |
| `py/pytanga/viz/serializer.py` | Add `serialize_object()` dispatcher; move label serialization to `_overlay.py`; `serialize_scene_update()` reverts to `(objects, removed)` |
| `py/pytanga/viz/server.py` | `FlushCallback` reverts to `(objects, removed)` 2-tuple |
| `py/pytanga/viz/visualizer.py` | `add()` creates `SceneObject` internally; `_flush_async()` delegates to single push; remove label-specific handling (labels are now overlay objects) |
| `py/pytanga/viz/templates/viewer.js` | Single `sceneObjects` Map; `upsertObject()` dispatcher; `buildOverlayElement()` for overlay kinds; remove `upsertLabel()`/`labelObjects` |
| `py/pytanga/viz/export/_html.py` | Bootstrap adapter uses single loop over `msg.objects`; dispatches on `layer` |
| `py/pytanga/viz/__init__.py` | No API changes (backward compatible) |

### 4.3 Lightly Modified Files

| File | Changes |
|------|---------|
| `py/pytanga/viz/_label.py` | `Label` dataclass unchanged; `get_label_anchor()` unchanged |
| `py/pytanga/viz/_styles.py` | `LabelStyle` unchanged |
| `py/pytanga/viz/_props.py` | Unchanged |
| `py/pytanga/viz/export/_gltf.py` | Unchanged (glTF has no overlay concept) |
| `py/pytanga/viz/templates/viewer.html` | Unchanged |
| `py/pytanga/viz/templates/controls.js` | Unchanged |

---

## 5. Implementation Checklist

### 5.1 `scene.py` — Unified Object Storage

- [ ] **S1:** Define `SceneObject` dataclass with `id`, `layer`, `kind`, `data`, `properties`, `dirty`
- [ ] **S2:** Replace `self._entities: Dict[str, SceneEntity]` with `self._objects: Dict[str, SceneObject]`
- [ ] **S3:** Replace `self._labels: Dict[str, Label]` + `self._label_order` with unified `_order` list
- [ ] **S4:** Implement `add_object(obj: SceneObject, *, object_id: str | None = None) -> str`
- [ ] **S5:** `add_object()` handles both `layer="scene"` and `layer="overlay"`
- [ ] **S6:** Implement `remove_object(object_id: str)`
- [ ] **S7:** Update `flush()` to return `(objects, removed)` — serializes all dirty objects regardless of layer
- [ ] **S8:** Update `full_state()` to return all objects (scene + overlay), not just entities
- [ ] **S9:** Remove `add_label()`, `remove_label()`, `update_label()`, `_serialize_labels()` methods
- [ ] **S10:** Update `clear()` to remove all objects
- [ ] **S11:** Remove `SceneEntity` dataclass (replaced by `SceneObject`)

### 5.2 `serializer.py` — Unified Dispatch

- [ ] **Z1:** Add `serialize_object(obj: SceneObject, *, defaults, styles_map) -> dict`
- [ ] **Z2:** `serialize_object()` dispatches on `obj.layer`:
  - `"scene"` → `_serialize_scene_entity()` (existing entity serialization, renamed)
  - `"overlay"` → `_serialize_overlay()` (new, imports from `_overlay.py`)
- [ ] **Z3:** Rename `serialize_entity()` → `_serialize_scene_entity()` (internal)
- [ ] **Z4:** Move `_serialize_label()` to `_overlay.py`
- [ ] **Z5:** `serialize_scene_update()` accepts `objects: list[dict]` and `removed: list[str]` (no separate labels param)
- [ ] **Z6:** All overlay serialization produces `layer: "overlay"` in output dict

### 5.3 `_overlay.py` — New File

- [ ] **O1:** Create `py/pytanga/viz/_overlay.py`
- [ ] **O2:** Implement `_serialize_overlay(obj: SceneObject) -> dict`
- [ ] **O3:** Dispatch on `obj.kind` for label, slider, button, control_group, etc.
- [ ] **O4:** Include `positioning: "world" | "fixed"` in overlay output
- [ ] **O5:** Include `parentId` when overlay object has a parent
- [ ] **O6:** Include `offset: [x, y, z]` for world-positioned overlays
- [ ] **O7:** Include `anchor` + `offset` (pixels) for fixed-position overlays

### 5.4 `server.py` — Simplified Callback

- [ ] **V1:** Revert `FlushCallback` to `tuple[List[Dict], List[str]]` (objects + removed)
- [ ] **V2:** `_push_full_state()` calls `serialize_scene_update(objects, [])` (no separate labels)
- [ ] **V3:** `push()` unchanged (already takes entities + removed — now objects + removed)

### 5.5 `visualizer.py` — Unified `add()`

- [ ] **W1:** `add()` creates a `SceneObject(layer="scene", kind=..., data=entity)` for entities
- [ ] **W2:** When `label="S1"` is provided, `add()` creates an additional `SceneObject(layer="overlay", kind="label", data=lbl)`
- [ ] **W3:** `viz.add(Label(...))` creates `SceneObject(layer="overlay", kind="label", data=label)`
- [ ] **W4:** `_flush_async()` calls `self._scene.flush()` → `(objects, removed)` → `self._server.push(objects, removed)`
- [ ] **W5:** Both `start()` and `run()` lambdas pass unified objects to `_push_full_state`
- [ ] **W6:** Remove label-specific logic from `add()` (the Label construction still happens but goes through unified path)

### 5.6 `viewer.js` — Unified Frontend

- [ ] **J1:** Replace `entityMeshes` + `labelObjects` Maps with single `sceneObjects` Map
- [ ] **J2:** Implement `upsertObject(msg)` — dispatches on `msg.layer`
- [ ] **J3:** `msg.layer === "scene"` delegates to existing `createEntityMesh()` → store in `sceneObjects`
- [ ] **J4:** `msg.layer === "overlay"` delegates to `buildOverlayElement(msg)` → optionally wrap in CSS2DObject
- [ ] **J5:** Implement `buildOverlayElement(msg)` — dispatches on `msg.kind`:
  - `"label"` → `createLabelElement(msg)` (existing label DOM logic)
  - Future: `"slider"`, `"button"`, `"color_picker"`, `"control_group"`
- [ ] **J6:** `msg.positioning === "world"` wraps DOM element in `CSS2DObject`, attaches to parent via `sceneObjects.get(msg.parentId)?.obj`
- [ ] **J7:** `msg.positioning === "fixed"` appends DOM element to `document.body` with absolute positioning + anchor
- [ ] **J8:** Update `handleMessage()` — process `msg.objects` instead of `msg.entities` + `msg.labels`
- [ ] **J9:** Update `removeEntityMesh()` to handle overlay objects (remove DOM elements, dispose CSS2DObjects)
- [ ] **J10:** Render loop unchanged (CSS2DRenderer already renders all CSS2DObjects in scene)
- [ ] **J11:** Export HTML bootstrap adapter uses single loop over `msg.objects` with layer dispatch

### 5.7 Export HTML

- [ ] **E1:** Update `_BOOTSTRAP_ADAPTER` in `_html.py` to iterate `msg.objects` instead of separate entity + label loops
- [ ] **E2:** Dispatch on `obj.layer` in the adapter: `"scene"` → `createEntityMesh()`, `"overlay"` → `buildOverlayElement()`
- [ ] **E3:** Labels rendered via unified path (same `buildOverlayElement` as live viewer)

### 5.8 Tests

- [ ] **T1:** Test `SceneObject` construction and defaults
- [ ] **T2:** Test `Scene.add_object()` with scene-layer object
- [ ] **T3:** Test `Scene.add_object()` with overlay-layer object
- [ ] **T4:** Test `Scene.flush()` returns scene + overlay objects together
- [ ] **T5:** Test `Scene.full_state()` returns all objects
- [ ] **T6:** Test `serialize_object()` for scene-layer entity
- [ ] **T7:** Test `serialize_object()` for overlay-layer label
- [ ] **T8:** Test unified WebSocket message format (`msg.objects` replaces `msg.entities` + `msg.labels`)
- [ ] **T9:** Test `visualizer.add(entity, label="S1")` still works (internally creates 2 SceneObjects)
- [ ] **T10:** Test `visualizer.add(Label(...))` still works
- [ ] **T11:** Test `visualizer.export_html()` produces valid HTML with labels via unified path
- [ ] **T12:** All existing 90+ tests updated and passing

### 5.9 Manual Verification

- [ ] **M1:** Smoke test: `viz.add(Point(...), label="P₁")` — label visible in live viewer
- [ ] **M2:** Smoke test: `viz.add(Label(...))` — standalone label visible
- [ ] **M3:** Smoke test: `viz.export_html()` — labels visible in exported HTML
- [ ] **M4:** Smoke test: All entity types still render
- [ ] **M5:** Smoke test: All operator types still render
- [ ] **M6:** Smoke test: Animation (`animate_to`, timeline) still works
- [ ] **M7:** Browser console: no errors, no warnings

---

## 6. Backward Compatibility

### 6.1 User-Facing API — NO Breaking Changes

```python
# All existing usage patterns continue to work unchanged:
viz.add(Point(1, 2, 3), ObjVizProps(color="#ff4444"), label="P₁")
viz.add(Label(text="Origin", position=(0, 0, 0)))
viz.add(s1_mv, _P(color="#ff4444"))

# New capabilities added (Phase 12+):
viz.add(Slider("opacity", min=0, max=1, value=0.8, parent_id=sphere_id))
viz.add(Button("Reset", action="reset_all", anchor="top-right"))
```

### 6.2 Internal API — Breaking Changes

- `Scene.entities` → `Scene.objects` (property, if exposed)
- `Scene.flush()` return type changes from `(entities, removed)` to `(objects, removed)`
- `FlushCallback` type changes from 3-tuple to 2-tuple
- WebSocket message key changes from `msg.entities`/`msg.labels` to `msg.objects`
- `viewer.js` internal Maps merged into single `sceneObjects`

These are all internal — no user code depends on them.

---

## 7. Relationship to Other Phases

| Phase | Impact |
|-------|--------|
| **4c** | Style classes unchanged; overlay objects may get their own styles in future |
| **4d** | `Label` and `LabelStyle` unchanged; they become overlay objects |
| **5/6** | JS renderers unchanged for scene-layer objects; new overlay renderers added |
| **7** | Animation unchanged; world-tracked overlays follow animated parents automatically |
| **11** | Export HTML adapter updated to iterate unified objects |
| **12+** (future) | Interactive controls (sliders, buttons) added as new overlay kinds |

---

## 8. Verification Checklist

- [ ] `SceneObject` dataclass defined with `id`, `layer`, `kind`, `data`, `properties`, `dirty`
- [ ] `Scene._objects` is the single source of truth (no parallel dicts)
- [ ] `Scene.flush()` returns unified `(objects, removed)`
- [ ] `serialize_object()` dispatches on `layer` correctly
- [ ] WebSocket messages use `msg.objects` key
- [ ] `viewer.js` uses single `sceneObjects` Map
- [ ] `upsertObject()` handles both `"scene"` and `"overlay"` layers
- [ ] Labels render identically to Phase 4d behavior
- [ ] Export HTML renders labels via unified path
- [ ] All existing tests pass (updated for new internal APIs)
- [ ] No user-facing API changes
- [ ] Browser console has no errors