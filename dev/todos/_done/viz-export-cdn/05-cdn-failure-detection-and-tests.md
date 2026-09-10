# Phase 5 — CDN-failure detection + tests

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Extend the export failure banner to catch a missing Tanga bundle, and lock in
all three delivery modes with targeted tests + an end-to-end smoke.

## Files

- Edit: `py/pytanga/viz/export/_bootstrap/_errors.py`
- Edit: `py/tests/viz/test_export_static.py`
- Edit: `py/tests/viz/test_export_cdn.py`
- Edit: `py/tests/viz/test_export_renderers.py` (if expectations changed)

## Steps

- [x] **5.1 — `js_cdn_check_script` essential-failure branch**
  - Also set `ESSENTIAL_FAILED` when `window.__tanga` is undefined after the
    module scripts run; update the banner copy to mention the Tanga viewer
    bundle alongside Three.js.
- [x] **5.2 — Static snapshot/figure delivery tests**
  - cdn: jsDelivr `gh` URL present, no `function createEntityMesh(` inlined.
  - inline: `function createEntityMesh(` present, no `gh` URL, import map present.
  - offline: `function createEntityMesh(` present, no `gh` URL, no import map,
    third-party JS inlined (e.g. `html2canvas` text present, no CDN `<script
    src>` for it).
  - Same for `render_figure`.
- [x] **5.3 — Animated export tests**
  - `render_export_animated_figure` / `render_export_animated_html` honour
    `delivery` and `delivery_ref`.
- [x] **5.4 — Resolver edge cases + `display_snapshot`**
  - `delivery_ref="feat/x"` / `"abc1234"` pass through unchanged; a dev version
    raises `ValueError`; an explicit override does not raise.
  - `Visualizer._render_snapshot_html("")` defaults to cdn (contains `gh` URL).
- [x] **5.5 — End-to-end smoke**
  - Build a `Visualizer` with entities; `export_snapshot` three times (cdn,
    inline, offline); assert the structural differences and that each writes a
    file.

## Validation

`uv run pytest py/tests/viz/test_export_static.py py/tests/viz/test_export_cdn.py py/tests/viz/test_export_renderers.py py/tests/viz/test_export_camera.py -q`

## Notes

- Keep the mode assertions in Python tests (no browser needed).
