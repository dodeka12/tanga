# Phase 2 — Bootstrap `_expandFrames` + embed the diff format

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/architecture/viz-architecture.md` (export bootstrap) and the generators
> in `py/pytanga/viz/export/_bootstrap/_animation.py`.  This phase changes the
> *serialized* shape and the generated bootstrap; it stays within the existing
> `window.__TANGA_ANIMATION__` seam (no new protocol).

## Goal

Emit `_expandFrames()` in the animated-export adapter and switch the export call
sites to `to_diff_dict()`, so exported HTML embeds `initial`+`deltas` and the
browser materializes full `frames[]` at load.  Legacy `frames` input keeps working.

## Files

- **Edit** `py/pytanga/viz/export/_bootstrap/_animation.py` (add `js_expand_frames()`, wire `js_animation_data_init`)
- **Edit** `py/pytanga/viz/export/_bootstrap/__init__.py` (export `js_expand_frames`)
- **Edit** `py/pytanga/viz/export/_animated_figure.py` (import + emit `js_expand_frames()` in both adapters)
- **Edit** `py/pytanga/viz/visualizer.py` (`_render_snapshot_html` / `_render_figure_html` use `animation.to_diff_dict()`)
- **Edit** `py/tests/viz/test_animation_export_diff.py`

## Steps

- [x] **2.1 — Add `js_expand_frames()` generator**
  - In `_bootstrap/_animation.py`, add a generator emitting the
    `function _expandFrames(animData) { … }` from the README contract, handling both
    `animData.frames` (legacy) and `initial`+`deltas`.
  - Export it from `_bootstrap/__init__.py` (alongside `js_animation_data_init`).

- [x] **2.2 — Wire `js_animation_data_init`**
  - Change the emitted `const frames = animData.frames || [];` to
    `const frames = _expandFrames(animData);`.
  - Leave `cameras`, `figMeshMap`, and `extra_map_vars` as-is.

- [x] **2.3 — Emit `js_expand_frames()` in the adapters**
  - Import `js_expand_frames` in `_animated_figure.py` from `_bootstrap`.
  - In both `_build_animated_figure_adapter` and
    `_build_animated_fullpage_adapter`, insert `js_expand_frames()` into the `parts`
    list immediately before `js_animation_data_init(...)`.

- [x] **2.4 — Switch export call sites to the diff dict**
  - In `visualizer.py`, change the animation branches of `_render_snapshot_html`
    (`→ render_export_animated_html(animation.to_diff_dict(), …)`) and
    `_render_figure_html` (`→ render_export_animated_figure(animation.to_diff_dict(), …)`).
  - `render_export_animated_html` / `render_export_animated_figure` signatures stay
    unchanged — they embed whatever dict they receive.

- [x] **2.5 — Tests**
  - `render_export_animated_html(rec.to_diff_dict())` contains `_expandFrames` and
    `"deltas"`, and (after decompressing the embedded payload) no repeated
    static-entity dicts.
  - `render_export_animated_html(rec.to_dict())` (legacy) still embeds `frames` and
    `_expandFrames` (string presence).
  - Expanding the embedded diff payload with the Phase-1 `expand()` reference equals
    `rec.frames`.

## Validation

```bash
uv run pytest py/tests/viz/test_animation_export_diff.py py/tests/viz/test_export_animation_transform.py -q
node js/dev/tests/check-syntax.mjs
```

## Notes

- `_expandFrames` is generated into the *adapter* (inlined in the HTML), not into the
  `window.__tanga` CDN bundle, so `tools/build-viewer-js.py` is **not** required here.
- Function declarations hoist, but emit `js_expand_frames()` before
  `js_animation_data_init(...)` anyway for clarity.
