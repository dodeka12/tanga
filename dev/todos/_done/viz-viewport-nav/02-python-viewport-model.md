# Phase 2 — Python viewport + navigation model

## Goal

Add the `Navigation` enum and `ViewportConfig` dataclass to `camera.py`, and
thread `navigation` / `controls` / `viewport` through `CameraView` and
`SceneView` (validation + serialization). Pure data + validation — no
server/frontend wiring yet.

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Files

- Edit: `py/pytanga/viz/camera.py`
- Edit: `py/pytanga/viz/views.py`
- New: `py/tests/viz/test_viewport.py`

## Steps

- [x] **2.1 — `Navigation` enum in `camera.py`**
  - Add `class Navigation(StrEnum)` with `ORBIT = "orbit"` and `VIEW2D = "2d"`,
    placed next to `CameraAction`/`CameraLock`.
- [x] **2.2 — `ViewportConfig` dataclass in `camera.py`**
  - `zoom: float = 1.0`, `pan: tuple[float, float] = (0.0, 0.0)`,
    `min_zoom: float | None = None`, `max_zoom: float | None = None`,
    `pan_xlim: tuple[float, float] | None = None`,
    `pan_ylim: tuple[float, float] | None = None`.
  - `__post_init__`: reject `zoom <= 0`; reject a `pan` tuple that is not two
    floats; reject inverted limits (`min_zoom > max_zoom`, `xlim[0] > xlim[1]`, …).
  - `to_dict()` emits the fixed contract shape from the README (omit `None`).
- [x] **2.3 — `CameraView` fields**
  - Add `navigation: str = "orbit"` (validated against `Navigation` values),
    `controls: dict[MouseButton, CameraAction | None] | None = None`, and
    `viewport: ViewportConfig | None = None` to `CameraView`.
  - `__post_init__` normalizes `navigation` (invalid value → `ValueError`).
  - `to_dict()` emits `navigation`, `controls` (same shape as
    `SceneConfig.controls`), and `viewport` (via `ViewportConfig.to_dict()`) —
    omitting defaults/`None`.
- [x] **2.4 — `SceneView` surface**
  - Add the same `navigation`/`controls`/`viewport` keyword arguments to
    `SceneView.__init__`, forwarded into its `camera_view` (mirroring how `lock`
    and `camera` are forwarded today).
- [x] **2.5 — tests (`py/tests/viz/test_viewport.py`)**
  - `ViewportConfig` defaults, validation errors, and `to_dict` (with/without
    limits).
  - `CameraView(navigation="2d", controls={…}, viewport=…)` serializes the new
    fields; defaults omit them; invalid `navigation` raises.
  - `SceneView(…, navigation="2d", viewport=…)` forwards to its `camera_view`.

## Validation

```
uv run pytest py/tests/viz/test_viewport.py -q
```

## Notes

- Reuse the existing `MouseButton` (`py/pytanga/viz/_interaction.py`) and
  `CameraAction` (`camera.py`) — do not introduce new button/action enums.
- Keep `camera.py` / `views.py` pure data + validation (no server imports).
