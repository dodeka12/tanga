# Changes in version 0.8.0

## New Features

- **Interactive 3D object manipulation** — pointer events (click, double-click,
  drag, scroll) on 3D entities are captured by the frontend and dispatched to
  user-registered async handlers on the backend via WebSocket. Includes:
  - `InteractionConfig` and `InteractionTrigger` dataclasses for configuring
    which pointer events an entity responds to.
  - `ClickEvent`, `DragEvent`, and `ScrollEvent` dataclasses with
    camera-aware world-space data and delta transform matrices.
  - Drag-move coalescing on the backend to prevent handler overload during
    rapid dragging.
  - Per-trigger `DragMode` (VIEW_PLANE, XY_PLANE, XZ_PLANE, YZ_PLANE) for
    constrained-plane dragging with modifier-key shortcuts.
  - Frontend module (`interaction.js`) with raycaster, throttling,
    pointer capture, and orbit-controls conflict resolution.

- **Active scene objects** (`ActSceneObject`, `ActPoint`) — self-registering
  interactive entities that set up their own interaction handlers with the
  visualizer.  `ActPoint` provides built-in drag-plane switching via standard
  modifier keys (Shift=XY, Ctrl=XZ, Ctrl+Shift=YZ, none=view-plane).

- **Active object styles** (`ActObjectStyle`, `ActPointStyle`) — dataclasses
  for controlling hover visual feedback (`hover_emissive`, `hover_scale`).

- **`viz.set_interaction()` and `viz.on_interaction()`** API on both
  `Visualizer` and `VizSceneHandle` for registering interaction configs
  and event handlers on entities.

## Breaking Changes

- **`Circle` parameter order changed** to `center, radius, normal, is_imaginary`
  (previously `center, normal, radius, is_imaginary`).

## Doc Changes

- Added `object-interaction.md` documenting the interaction system architecture
  and API.
- Added `active-elements/index.md` and `active-elements/act-point.md`
  documenting active scene objects and `ActPoint` usage.
- Added demo examples: `demo_drag_point.py` and `demo_act_point.py`.