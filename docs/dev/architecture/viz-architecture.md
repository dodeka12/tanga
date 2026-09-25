# Viz architecture

Canonical overview of the Tanga viewer (`py/pytanga/viz/`) after the
scene/layout/overlay remodel.  It documents the **ownership hierarchy**, the
**data flows**, and the **extension recipes** (new entities, new `*View`
controls, new overlay objects like `Dialog`/`Banner`).  Written for developers
and for AI agents: read the invariants + file map before touching code.

## Big picture

One hierarchy, one owner per concern — no parallel global-registry dicts.

```
Visualizer                facade + composition root + lifecycle (boot/loop)
|- Transport             WebSocketTransport: send / register / route / dispatch
|- LayoutHost            owns scenes AND layouts (+ register/resolve/dispatch)
|   |- scenes:  dict[name, Scene]        entity containers (add_scene)
|   `- layouts: dict[name, Layout]       first-class layouts (set_layout)
|       `- Layout { base: View, overlay: OverlayContainer }
|- ThemeHost / InteractionHost
`- OverlayContainer      per-layout: overlays, dialogs, banners, editor
```

There is **no `ControlHost`**.  Each `*View` wraps a `Control` that owns its own
value, serialization, and handlers (`serialize` / `register_handlers` /
`handle_event`); `LayoutHost` owns the tree walk that registers them and the
inbound dispatch that resolves them.

- **`Scene`** owns *entities* and the typed entity API.  One scene can appear in
  many panes (`SceneView(name)`) and many layouts.
- **`Layout`** is a `base` view tree plus an `OverlayContainer`.  URLs name
  **layouts** (`/?view=<name>`), never scenes.
- **`Visualizer`** wires everything together and exposes the public `viz.*` API
  through explicit thin forwarders (no `__getattr__`).

## Ownerships

| Concern | Owner | Notes |
|---|---|---|
| named scenes | `LayoutHost.scenes` | `add_scene(name)` auto-creates `Layout(name, SceneView(name))` |
| named layouts | `LayoutHost.layouts` | `set_layout(root, name)` / `add_layout(root, name)` |
| base view tree | `Layout.base` | `SplitView` / `StackView` / `SceneView` |
| view identity | `View.id` (auto `v0`…, overridable via `id=`) | stable across re-serializations; `remove_view(id)` |
| overlays (groups/dialogs/banners/editor) | `Layout.overlay` (`OverlayContainer`) | one per layout (shared instance today) |
| entities | `Scene` (`add_viz`/`add`/`update`/`remove`/`clear`) | |
| styles | `Scene.styles` (copy of the master `_global_styles`) | |
| control model (value/handlers/history) | the `Control` on each `*View` | `view.control` |
| `(id, event)` handlers | `ControlHandlerRegistry` (via `Transport`) | registered by `Control.register_handlers` |
| inbound routing | `Transport.route` data table -> `LayoutHost.dispatch_control_event` | |

## Data flows

- **Boot** — `Visualizer.__init__` builds `Transport` -> `LayoutHost`
  (+`add_scene("")`) -> `ThemeHost`/`InteractionHost`; `OverlayContainer` gets a
  back-reference to its owning `LayoutHost`, then `_register_routes()`.
- **URL -> layout** — `/` serves the `""` layout, `/?view=<name>` serves
  `layouts[name]`; `add_scene(name)` supplies scene-URL sugar for free.
- **Add an entity** — `viz.add(...)` -> `layout.scene("").add_viz(...)` ->
  `Scene.add`/`add_object` -> `SceneObject` + `VizNode` -> `flush()` -> `entity_*`
  messages.  `_resolve_scene_entity` turns MVs into `SceneEntity` (and refines
  a raw `Conic` to its specific 2D entity so the viewer can serialize it;
  `Quadric3D` is left alone and renders via the analytic ray path).
- **Insert a detached subtree** — a `VizGroup`/`VizSceneObject` tree composed
  *before* any scene exists is added via `viz.add(group)`/`viz.new(group)` →
  `Scene.add_viz` → `Scene.add_subtree`, which registers every descendant in
  `_nodes` (auto-assigning ids where omitted) and backfills each node's partial
  style from the scene's per-kind defaults.
- **Add a control** — build a `*View`, mount it via `set_layout` (or declaratively
  in `SceneView(overlay=[...])`); `LayoutHost.register` walks the tree and calls
  each `Control.register_handlers` (registers `(id, event)` handlers).
- **Inbound control event** — `control:*` -> `LayoutHost.dispatch_control_event` ->
  `resolve_control` **tree-walk** (layouts + dialogs) -> `control.handle_event`
  -> `Dispatch(event, value, push)` -> push + fire the handler.
- **Banner/dialog/editor** — `OverlayContainer.show_*` registers `(id, event)`
  handlers and sends `banner_*`/`dialog_*`/`editor_*` wire messages; the
  `*_closed`/`accept`/`close` routes call `OverlayContainer._on_*`.
- **Add/remove an overlay view** — `viz.add(view)` mounts a `View` in the
  global overlay and pushes a granular `overlay_define` (only that view, not
  the whole layout); `viz.remove_view(id)` removes it via `overlay_remove`.
  Per-scene overlays (`scene=…`) re-sync the layout instead.  Every `View`
  carries a stable `id` (auto `v0`…) so it can be addressed at runtime.
- **Layout re-push** — the frontend **reconciles the whole view tree by stable
  view id** across `view_layout` re-pushes. A single live-view registry
  (`_viewRegistry`) reuses each view whose id is unchanged (scene panes keep
  their WebGL scene/camera; simple controls keep their DOM), and only views that
  are added or removed are created/torn down. Containers are rebuilt (cheap DOM)
  and re-attach the reused children in the new order, so reordering a layout
  re-parents the expensive panes instead of destroying them. A scene pane newly
  introduced by a re-push fetches its state with a `scene_sync_request`
  round-trip.

## Canonical frame + transform placement

Every scene entity renders in a **canonical frame** and its placement rides on a
single per-entity `Transform` (quaternion TRS) applied to the per-entity
`THREE.Group` that already wraps each mesh (`wrapWithNodeTransform` /
`applyTransformToObject` in `scene-builder.js`).  There is no second, baked
placement in the renderers or the content serialization — this is what makes a
`Circle`-center change a cheap `transform` patch rather than a content
re-serialization.

- **Canonical frames** (three.js defaults): linear primitives (`Line`,
  `Cylinder`, `Cone`, `Direction`, `Parabola`, `Hyperbola`) along **+Y** with
  their origin at the node position; planar primitives (`Circle`, `Arc`, `Disk`,
  `PartialDisk`, `Ellipse`, `RegularPolygon`, `Rectangle2D`, `Plane`) in the
  **XY** plane (normal **+Z**) centred at the node position; volumes (`Sphere`,
  `Box`, `Ellipsoid`) centred at the node position, axis-aligned (`Box`/
  `Ellipsoid` `rotation` → quaternion); `Point`/`HPoint` at the node position.
- **Decomposition** — `_decompose.py::_entity_decompose(entity)` maps an
  entity's placement into a `(Transform, shape)` pair: `center`/`origin`/
  `vertex`/`point` → position; `normal`/`axis`/`direction` (+ `startDirection`/
  `dirU`/`dirV`/`horizontal` where a second axis fixes the frame) → quaternion;
  `rotation` (Box/Ellipsoid) → quaternion; everything else → shape params.  The
  scene-graph node (`VizSceneObject.__init__`) derives its `transform` from this
  decomposition, and `set_entity` re-derives it and diffs shape vs placement
  with a configurable epsilon (default `1e-9`): `transform` on placement change,
  `content` on shape change, `full` on kind change.  Out-of-scope kinds
  (`PointPath`/`Curve`/`PointSet`, point/plane pairs, operators, axes/grid,
  SDF/ray/image) return `(Transform(), {})` and rebuild on any change.
- **Wire contract** — the serializer emits **shape-only** content (no
  `center`/`normal`/`axis`/`origin`/`direction`/`vertex`/`rotation`/
  `startDirection`); placement rides on the node `transform`, whose `rotation`
  is a quaternion `[x, y, z, w]` (`Transform.to_dict()`).  `serialize_entity()`
  emits the same `transform` for direct callers.  The glTF exporter reads the
  node `transform` (position + quaternion) rather than re-deriving it from
  geometry.
- **`Transform` location** — `Transform` and the argument-coercion helpers live
  in `geometry/transform.py`; the pure matrix/quaternion math in
  `geometry/transforms.py`; `viz` keeps thin re-export shims
  (`viz/_transforms.py`, `viz/_types.py`) and re-exports `Transform` publicly.
  `Transform.rotation` is a quaternion (single source of truth), the `matrix()`
  is computed lazily, and `Transform` overloads `@`/`*` to apply to `Point`
  (`R·S·p + t`) and `Direction` (`R·S·d`, no translation).
- **`Frustum`** is re-parameterized intrinsically (`origin`, `axis`,
  `horizontal`, `near`, `far`, `far_half_width`, `far_half_height`) so it
  participates in transform placement and diffing like the other entities.

## Extension recipes

### New entity kind

1. Add the `SceneEntity` (or reuse `SceneObject` for non-geometry drawables).
2. Route it through `Scene.add_viz` — it already handles `color`/`opacity`/
   `style`/`label`/`parent_id`/`attach_to`; note `_resolve_scene_entity` for MV
   analysis (multivector -> `SceneEntity`).
3. Serialize it in the node layer (`VizSceneObject`/`SceneObject` in
   `scene.py` / `_nodes.py`).
4. Add a frontend renderer + a test (round-trip + flush).
5. Export an `update<Kind>(mesh, ent, prev)` from the renderer module (return
   `false` to rebuild) for kinds whose geometry derives from content fields, so
   a live content change re-samples/re-builds the mesh instead of falling
   through to the flat `entityRequiresRebuild` field list.  Wire it into
   `factory.js::updateEntityMesh`.

### New control (`*View`)

1. `Control` dataclass in `_controls.py` with `_value_type` + `_fields()`
   (scalar controls) or `set_value`/`get_value` overrides (`Table`).  No
   central switch — `serialize()` merges `_fields()`.
2. `*View(ControlView)` in `views.py` whose `__init__` builds
   `self.control = <Control>(...)` (keep the constructor signature;
   `ControlView.__getattr__` forwards reads and `set_value`/`undo`/`redo` to the
   control; `ControlView.set_value` sets *and* pushes `control_update`).
3. `Control.handle_event(event, payload) -> Dispatch` for any new event or model
   mutation (see `Table.handle_event`).  The `on_*` fields *are* the handler
   declaration — `Control.register_handlers` maps `on_change` -> `"change"`, etc.
4. Frontend factory + `sendEvent(id, event, {value})`; add a server
   `_EVENT_MSG_MAP` entry for a new message name.
5. Tests: serialization round-trip, handler registration, dispatch.

### New overlay object (Dialog/Banner pattern)

Follow the `OverlayContainer` pattern exactly:

1. State in `OverlayContainer.__init__`:
   `self._things: dict[str|None, dict[str, Any]] = {}` + a counter.
2. Add `_next_*_id`, `_register_*`, `show_*`/`remove_*`/`clear_*` (+ `_async`
   variants using `await self._transport.send_async`), `_push_*` serializers,
   and `_on_close`/`_on_accept` handlers.
3. Register handlers via `self._transport.register(id, handler, event=...)`; use
   `self._layout` (the owning `LayoutHost`) to register dialog content and
   resolve control ids.
4. Add the inbound route in `Visualizer._register_routes` -> an
   `OverlayContainer._on_*` method; add `Visualizer.show_*`/`remove_*` forwarders.
5. Test the wire round-trip + handler lifecycle.

## Invariants + AI-agent orientation

- Every `id` is globally unique; `(id, event)` is the single handler key.
- Every `View` has a stable `id` (auto `v0`…, overridable via `id=`); its
  `_serialize()` emits `self.id` — there is no per-serialization id generator.
- `viz.remove_view(id)` removes a mounted overlay view (global overlay = a
  granular `overlay_remove`; per-scene overlay = a full re-sync).
- Controls live in **overlays/layouts**, never in `Scene`.
- No `add_*` facades and no runtime value API; value/history/serialization/
  handler registration live on the control (`Control.set_value`,
  `Control.serialize`, `Control.register_handlers`, `Table.undo`/`redo`).
- Inbound dispatch **walks the layout tree** (`LayoutHost.resolve_control`);
  there is no `_control_views` index and no `ControlHost`.
- `Visualizer.add` is **polymorphic**: a `View` -> the default layout overlay,
  everything else -> the main scene.

### Layout reconciliation & runtime updates (frontend)

The frontend has **one live-view registry** and reuses views by their stable
`id` — do not build a second, parallel structure.

- **One `_viewRegistry`.** `templates/viewer.js` keeps a single
  `_viewRegistry: Map<view_id, View>` of every live view. `_sceneRoutes`
  (scene → panes) and `_viewById` (view_id → `ThreeJsView`, the target of the
  `view_camera`/`view_viewport`/`view_background_image` dispatch) are **derived**
  routing indexes recomputed from the built tree, not separate registries.
  `_controlRegistry` (control value/apply, owner-scoped) is a different concern
  and stays separate — it is not an orphan map.  If you need to look a view up
  by id at runtime, derive it from the tree/`_viewRegistry`; never add another
  id-indexed dict.
- **Reconciliation by id.** `buildViewTree` (`templates/views/build.js`)
  reuses a live view when `node.id` matches an existing view of the same type,
  refreshing it via `update(node)` (controls) / `updateFromNode(node)` (scene
  panes); a new id constructs a new view, and an id no longer present is torn
  down.  Containers are rebuilt (cheap flexbox DOM) and re-attach the reused
  children in order — `appendChild` moves the DOM node, so a reordered layout
  re-parents the expensive WebGL panes instead of recreating them.  The stateful
  `table`/`file_chooser`/`log` leaves are deliberately recreated (their
  `destroy()` unregisters file-browser/log state).
- **Identity = `View.id`.** The serialized `node.id` is the stable key. Reusing
  the same Python `View` object across `set_layout` keeps the frontend view
  alive; constructing a new `View` gets a new id, and the old frontend view is
  replaced.  There is no per-serialization id generator, so never re-key on
  scene name or positional index.
- **Granular updates, not a layout re-push.** For a single-value change, send a
  granular message — `view_camera`, `view_viewport`, `view_background_image`
  (per-pane, dispatched through `_viewById`), `control_update`/`log_update`
  (controls/logs), or `scene_update` (entities) — and re-push `view_layout` only
  for structural layout changes.  A new per-pane runtime knob must follow this
  pattern (a `view_*` message dispatched through `_viewById`), not a new
  full-tree channel.

### File map

| File | Role |
|---|---|
| `visualizer.py` | `Visualizer` — facade, composition root, lifecycle |
| `_layout.py` | `Layout`, `OverlayContainer`, `LayoutHostImpl` |
| `scene.py` | `Scene`, `SceneObject`, `SceneConfig`, `_resolve_scene_entity` |
| `_hosts.py` | `ThemeHost`, `InteractionHost`, `OverlayHost` |
| `_ids.py` | `generate_id()` — the single id convention shared by `_nodes.py` and `scene.py` |
| `_nodes.py` | `VizNode`/`VizSceneObject`/`VizOverlayObject`/`VizGroup`/`VizImage` scene-graph nodes |
| `_controls.py` | `Control` + subclasses (value/serialize/handle_event/register_handlers), registry |
| `views.py` | `View` + `SceneView`/`StackView`/`GroupView`/`MenuView` + `*View` |
| `_ports.py` | `Transport`/`LayoutHost` protocols + `ServerState` |
| `_transport.py` | `WebSocketTransport` |
| `_scene_handle.py` | `VizSceneHandle` (per-scene proxy) |
| `image.py` | `ImageData`/`ImageDType`/`ImageChannelMode` value model + `pil_to_numpy` |
| `_image_view.py` | `ImageView` (plane + textures + shader/uniform state) + `ImageCanvas` (dedicated 2D scene) |
| `_image_wire.py` | binary image-frame codec (server → client), v2 with a `codec` byte |
| `_image_pyramid.py` | `ImagePyramid` — on-demand tile pyramid (level/tile geometry + encode + LRU) |
| `_camera_stream.py` | `CameraStream` — MJPEG publisher (JPEG encode + latest-frame fan-out) |
| `_scale.py` | `Scale`/`nice_linear_ticks`/`log_ticks` — data↔world + tick math |
| `_coordinate_system.py` | `CoordinateSystem` plotting helper (axes/grid/overlay/underlay specs) |
| `templates/nice-ticks.js` | pure tick math port of `_scale.py` (Node-testable) |
| `templates/axes-overlay-math.js` | pure world↔data + tick/px layout math (Node-testable) |
| `templates/axes-overlay.js` | SVG axes-frame renderer (overlay layer) |
| `templates/grid-underlay.js` | SVG grid renderer (underlay layer) |

### Image canvas (extension recipe)

`ImageCanvas` (in `_image_view.py`) is a user-facing helper analogous to
`CoordinateSystem`: it owns a **dedicated 2D scene** with a **y-down pixel
frame** (1 world unit = 1 pixel), an `ImageView` (the plane + textures +
shader/uniform state), an `ActImagePlane` (interactive plane), and an overlay
`VizGroup`.  The image is a **new scene-object kind** (`kind == "image"`,
`VizImage` node in `_nodes.py`), whose pixel bytes travel as **binary WebSocket
frames** (`_image_wire.py`, `Transport.send_bytes` / `server.push_bytes`) with a
versioned **codec** byte (v2): `raw` / `jpeg` / `zlib` — auto-selecting JPEG for
8-bit 1/3-channel and lossless zlib otherwise, overridable via
`ImageData(codec=…)`.  Uniforms and overlays travel as JSON (`image_update`) and
never re-send the image.  Very large images are served as an **HTTP tile
pyramid** (`_image_pyramid.py`, `/image/{id}/{level}/{x}/{y}`, `source:
"tiled"`); camera feeds are served as **MJPEG** (`_camera_stream.py`,
`/stream/{id}`).  The export path stores images in an id-keyed **asset store**
(`AnimationRecording.assets`, `capture_frame(include_images=False)`), embedding
8-bit images as JPEG data URLs by default.

The same 2D scene hosts interactive rectangles: `Rectangle2D` (a new viz-only
entity, `kind == "Rectangle2D"`, rendered by `renderers/rectangle2d.js` as an
outline + optional fill) and `ActRectangle2D` (a composite `ActSceneObject` that
spawns square `ActPoint` handles for resize/translate).  Drag-to-create is shown
in the `rectangle_labeling.py` example by composing a disabled left-drag binding
plus a mode flag (no bespoke `draw_rectangle()` helper).

### Overlay coordinate system (extension recipe)

`CoordinateSystem(display_mode="overlay")` (2D only, no explicit `size`) draws the
axes as a fixed screen-space **overlay** frame and the grid as a **scene-level
underlay** behind the data.  The backend emits two payload-style scene objects —
`layer="overlay", kind="axes_overlay"` and `layer="underlay", kind="grid_underlay"`
(a generalized `VizOverlayObject` carrying a static `spec` of scales, formats,
labels, and styles) — instead of world-space `Axis`/`Grid` entities.  The data
group, transform, and `fit_view2d` camera ownership are unchanged.

The frontend layers each pane as `underlay container (z:0) → WebGL canvas (z:1,
transparent) → CSS2D labels (z:2) → overlay DOM (z:3)`.  `axes-overlay.js` (SVG
frame) and `grid-underlay.js` (SVG grid) recompute their ticks every frame from
the live ortho camera via the pure `nice-ticks.js` / `axes-overlay-math.js`
modules (ports of `_scale.py`).  Zoom/pan happens entirely in the browser
(`OrbitControls`), so the overlay reads the camera rather than round-tripping.

Export bundles those modules into `js/tanga-viewer.js` (CDN + `inline`/`offline`)
and the export adapters run the same renderers in their render loops; a
`grid_underlay` present makes the scene background transparent so the grid shows
through.

### Calibrated camera view (extension recipe)

A real camera's internal (`K`) + external (`R`, `t`) calibration drives a scene
pane through a clean three-layer model — camera data → camera view → pane:

- **`PinholeCamera`** (camera data, `type: "pinhole"`) — a sibling of
  `CameraConfig2d`/`CameraConfig3d` carrying intrinsics (`fx/fy/cx/cy/width/
  height`), pose, clipping, and a `fit` policy (`"fit"` letterbox / `"fill"`
  stretch).  `pinhole_camera(K, R, t, image_size=…)` builds it.
- **Coordinate frames + calibration types** (`pytanga.geometry` /
  `pytanga.viz.camera`) — a plain numeric `Matrix` (with a runtime-checkable
  `MatrixProvider` protocol), `CoordinateFrame`/`OpenCVFrame` axis conventions
  (OpenCV x-right/y-down/z-forward is a 180° rotation about +x, preserving the
  right-handed internal world), and `CameraCalibration(K, R, t, image_size,
  frame=OpenCVFrame(), units=…)` which converts read-in calibration to the
  standard frame + units and builds a `PinholeCamera`.  Frames satisfy
  `MatrixProvider`, so `set_transform(frame)` remaps OpenCV-frame data through
  the scene graph.
- **`pinhole-framing.js`** — a single pure module that maps the intrinsics +
  pane aspect + `fit` to both the off-center frustum bounds and the background
  quad's letterbox half-extents (`{hx, hy}`).  One source of truth for aspect,
  used by `applyPinhole(camera, aspect)` in `view_mode.js` on switch and resize.
- **`CameraView`** (presentation) — bundles the camera, a `lock` set (validated
  against `CameraLock`), a `navigation` mode (`"orbit"` default / `"2d"` dolly
  zoom + screen-space pan, no orbit), a per-pane `controls` button mapping, an
  optional `viewport` (`ViewportConfig`: `zoom`/`pan` + limits), and an optional
  `background_image`; serialized in the `scene_view` node as one `camera_view`
  field.
- **Viewport navigation** — a pane's 2D viewport (`{zoom, pan}`) is a
  presentation-layer transform folded into the pinhole crop window by
  `pinhole-framing.js` (returning both the sub-frustum and the background crop
  `{u0,v0,u1,v1}`), so projection and image never diverge.  Set at runtime via
  `Visualizer.set_viewport(view, …)` (per-pane `view_viewport` message, mirroring
  `view_camera`) or `set_viewport(scene_name=…)` / `VizSceneHandle.set_viewport`
  (scene-wide `SceneConfig.viewport` default).
- **Image background** — `CameraView.background_image` mounts a full-viewport
  NDC quad (`renderers/image-background.js`) that letterboxes to match the
  projection (and crops to the viewport window).  Pixel bytes travel on the
  existing binary frame transport (`_image_wire.py` →
  `LayoutHost.background_image_frames` → re-sent on connect), compressed with
  the same v2 codec; a `source: "tiled"` background fetches `/image/…` tiles
  and a `/stream/…` url streams MJPEG.  At runtime
  `Visualizer.set_background_image(view, image)` sends the new pixel frame
  followed by a granular `view_background_image` message — no `view_layout`
  re-push, so other panes are untouched.
- **Per-pane visibility** — `SceneView(hide=…, show=…)` filters which entities a
  pane builds (each pane has its own object registry, so no scene duplication).
- **Runtime entity visibility** — `Scene.set_visible` /
  `Visualizer.set_visible(…, scene_name=…)` / `VizSceneHandle.hide` set a node's
  `visible` flag and emit a granular `visible` aspect patch on the `object_update`
  channel (frontend sets `THREE.Object3D.visible`), so toggling visibility never
  re-serializes geometry/style.  Action objects add
  `ActSceneObject.set_enabled/enable/disable`, which flips
  `InteractionConfig.enabled` and re-pushes the existing `interaction` aspect.
- **Frustum** — `pytanga.geometry.Frustum` (a viz-only entity, no MV) with
  `Frustum.from_camera(camera)` and `FrustumStyle`; serialized to explicit
  corners and rendered by `renderers/frustum.js`.

### Test commands

```
uv run pytest py/tests/viz -q   # fast
uv run pytest -q                # full
uv run mkdocs build --strict    # docs
```

### Common pitfalls

- **Circular imports** — `scene.py` <-> `_scene_handle.py`; import `VizSceneHandle`
  and view classes lazily *inside* methods.
- **`Scene._host`** is a back-reference to the `Visualizer`, used only for
  `ActSceneObject` init and `VizSceneHandle` creation.
- **`OverlayContainer.configure(...)`** wires `transport`/`layout`
  post-construction (the layout host back-reference).
- **`set_layout` vs `add_layout`** — both take `(root, name="")`;
  `add_layout` raises if the name is taken; `set_layout` also registers
  handlers + injects `_push` callbacks and re-syncs the layout.
