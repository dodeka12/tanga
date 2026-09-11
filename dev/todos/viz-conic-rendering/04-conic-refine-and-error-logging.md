# Phase 4 — Auto-refine Conic + stop swallowing errors

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture. If this
> work introduces or changes architecture, update the developer docs.

## Goal

Make `viz.add(raw_conic)` work by refining the `Conic` to its specific entity in
the viz resolver, and surface (instead of silently dropping) serialization errors
so a bad scene no longer renders blank.

## Files

- Edit: `py/pytanga/viz/scene.py` (`_resolve_scene_entity`)
- Edit: `py/pytanga/viz/server.py` (WebSocket `_push_full_state` handler)
- New/Edit: `py/tests/viz/test_conic_renderers.py` (resolve + refine test)

## Steps

- [ ] **4.1 — Refine `Conic` in `_resolve_scene_entity`.**
  - At the top of `_resolve_scene_entity`, before the `SceneEntity` passthrough:
    `from pytanga.geometry.entities import Conic; if isinstance(obj, Conic):
    from pytanga.geometry import refine; return refine(obj)`.
  - Do **not** refine `Quadric3D` (it renders via the ray path). Let `refine`'s
    `ValueError` (imaginary/point-pair conic) propagate as the "raise" behavior.
- [ ] **4.2 — Log the silent WebSocket full-state failure.**
  - In `server.py`, replace the bare `except Exception: pass` around
    `await self._push_full_state(...)` with `except Exception: logger.exception(
    "full-state push failed", exc_info=True)` (keep the no-crash behavior).
- [ ] **4.3 — Tests.**
  - `_resolve_scene_entity(Conic(...))` returns the refined entity (e.g.
    `Ellipse`); `_resolve_scene_entity(Quadric3D(...))` returns the `Quadric3D`
    unchanged; a user `ConicStyle` + refine resolves to the merged style
    (user fields win) via `_style_to_output`.

## Validation

`uv run pytest py/tests/viz/test_conic_renderers.py py/tests/viz/test_scene_session.py -q`

## Notes

- `update_entity` / `VizSceneHandle.update_entity` already route through
  `_resolve`, so they inherit the refine behavior for free.
- The style merge (default for refined kind + user `ConicStyle`, user wins) is
  already implemented by `_style_to_output` in `_make_scene_node`; Phase 4 only
  adds a test to lock it in.
