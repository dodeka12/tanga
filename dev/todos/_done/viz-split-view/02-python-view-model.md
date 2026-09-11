# Phase 2 — Python `View` model + `view_layout` serialization

## Goal

A declarative, serializable `View` hierarchy mirroring the fixed wire contract.
Split-agnostic base; `SplitView` as one container; leaves for scene/control/
spacer. No rendering here — only data, validation, and serialization.

## Steps

- [x] **2.1 — Add `py/pytanga/viz/views.py`: `View` base**
  - `View` with per-axis fields: `preferred_width/height`, `min_width/height`,
    `max_width/height` (all `SizeSpec`), plus a `size: SizeSpec` convenience
    that sets both preferred axes.
  - `fixed_x`/`fixed_y` computed properties (`min == max`, both set) — the
    "fixed size" mechanism (no separate `fixed` flag).
  - `_serialize()` emitting the node shape (id, type, per-axis sizes).

- [x] **2.2 — `SplitView`**
  - `orientation: Literal["horizontal", "vertical"]`, `children: list[View]`,
    `movable: bool | None = None`, `sizes: list[SizeSpec] | None = None`.
  - Validation: ≥2 children; orientation is horizontal/vertical; `sizes` length
    matches children when provided.
  - `_serialize()` nests children recursively; assigns stable node ids.

- [x] **2.3 — Leaves: `SceneView`, `ControlGroupView`, `SpacerView`**
  - `SceneView(scene: str | VizSceneHandle)` → normalizes to the scene name.
  - `ControlGroupView(scene, group_id=None)` → resolves a scene name and an
    optional specific group id.
  - `SpacerView` — empty, fully flexible.

- [x] **2.4 — Layout tree helpers**
  - `serialize_layout(root: View, name: str) -> dict` producing the
    `view_layout` message.
  - `iter_scene_names(root) -> list[str]` (deduplicated, DFS order) — used by
    the server to subscribe and by `Visualizer` to build the URL.

- [x] **2.5 — Unit tests `py/tests/viz/test_views.py`**
  - Serialization shape matches the README contract (spot-check JSON).
  - Nested split round-trip; scene-name collection; validation errors
    (1 child, bad orientation, sizes length mismatch).

- [x] **2.6 — Export public symbols**
  - Add `View`, `SplitView`, `SceneView`, `ControlGroupView`, `SpacerView`,
    `Size`, `SizeSpec` to `py/pytanga/viz/__init__.py` + `__all__`.

- [x] **2.7 — Validate**
  - `uv run pytest py/tests/viz/test_views.py -q` and
    `uv run python -c "from pytanga.viz import SplitView, SceneView, Size"`.

## Validation

`uv run pytest py/tests/viz/test_views.py -q`

## Notes

- `views.py` is pure (no rendering/server imports) so it stays unit-testable in
  isolation and is the single source of truth for the wire shape.
