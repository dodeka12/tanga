# Phase 1 — Views API type cleanup

## Goal

Two small, self-contained type-hygiene changes in `views.py`: type
`SceneView`'s scene parameter as a concrete union `str | Scene |
VizSceneHandle`, and replace the `Orientation` string-literal alias with an
`EOrientation` StrEnum.

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Files

- Edit: `py/pytanga/viz/views.py`
- Edit: `py/tests/viz/test_views.py`

## Steps

- [x] **1.1 — Concrete `SceneRef` union**
  - `views.py` already has `from __future__ import annotations`; add
    `from typing import TYPE_CHECKING` and, under `if TYPE_CHECKING:`, import
    `Scene` (`.scene`) and `VizSceneHandle` (`._scene_handle`).
  - Define `SceneRef = str | Scene | VizSceneHandle` (module-level alias guarded
    so it resolves for type checkers without a runtime import).
  - Change `_coerce_scene_name(scene: SceneRef) -> str` and
    `SceneView.__init__(scene: SceneRef, ...)`; keep the runtime
    `getattr(scene, "name", ...)` duck-typing unchanged.
- [x] **1.2 — `EOrientation` enum**
  - Replace `Orientation = Literal["horizontal", "vertical"]` with
    `class EOrientation(StrEnum): HORIZONTAL = "horizontal"; VERTICAL = "vertical"`.
  - `SplitView.__init__(orientation: EOrientation | str, ...)`: coerce via
    `self.orientation = EOrientation(orientation)` (replaces the manual
    `if orientation not in (...)` check).
  - `SplitView._serialize`: `result["orientation"] = self.orientation.value`.
  - Leave `SeparatorView`'s inline `Literal["auto", "horizontal", "vertical"]`
    unchanged (its `"auto"` state is a separate concern).
- [x] **1.3 — tests**
  - Add: `SceneView(handle)` / `SceneView(scene_obj)` resolve to the same
    `.scene` name as `SceneView("name")`.
  - Update `test_bad_orientation` to expect `EOrientation`'s `ValueError` on an
    invalid value.

## Validation

```
uv run pytest py/tests/viz/test_views.py -q
```

## Notes

- No runtime behaviour change for scene resolution (still duck-typed); the union
  is the type-checker contract.
- Serialize the enum via `.value` (safer than `EStackDirection`'s raw
  pass-through across Python 3.11/3.12 `StrEnum` `str()` behaviour).
