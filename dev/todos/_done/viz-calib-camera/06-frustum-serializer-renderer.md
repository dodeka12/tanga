# Phase 6 — `Frustum` serializer + renderer

## Goal

Serialize `Frustum` as a new `kind: "Frustum"` entity (explicit corners), pass it
through `_resolve_scene_entity` without analysis, render it with a new
`renderers/frustum.js`, and dispatch it from `factory.js`.

## Files

- Edit: `py/pytanga/viz/serializer.py` (`_serialize_frustum` + entity dispatch)
- Edit: `py/pytanga/viz/_types.py` (add `Frustum` to the `SceneEntity` union)
- Edit: `py/pytanga/viz/scene.py` (confirm `_resolve_scene_entity` passthrough)
- New: `py/pytanga/viz/templates/renderers/frustum.js`
- Edit: `py/pytanga/viz/templates/renderers/factory.js` (`case 'Frustum'`)
- Edit: `py/pytanga/viz/export/_bootstrap/_html.py` (register `frustum.js` in `_RENDERER_FILES`)
- New: `py/tests/viz/test_frustum.py`

## Steps

- [x] **6.1 — serialize**
  - `_serialize_frustum(ent, props, ...)` → `{ "kind": "Frustum", "apex": bool,
    "near": [4×[x,y,z]], "far": [4×[x,y,z]] }` (apex = 4 identical near corners).
  - Add the `isinstance(entity, Frustum)` branch to the entity dispatch.

- [x] **6.2 — `SceneEntity` union + resolve passthrough**
  - Add `Frustum` to the `SceneEntity` union in `_types.py`.
  - Verify `_resolve_scene_entity` returns it as-is (it is a `SceneEntity`, never
    analyzed to an MV). Add a test that `viz.add(Frustum(...))` does not attempt
    `analyze`.

- [x] **6.3 — `frustum.js` renderer**
  - `createFrustum(ent)` / `updateFrustum(mesh, ent, prev)`: always draw 4 corner
    lines (apex → 4 far corners when `apex`); draw the near/far plane outlines;
    when `fill`, draw translucent end faces (and side faces when both ends are
    rectangles). Honor `thickness`, `opacity`, `fill_opacity`.

- [x] **6.4 — factory dispatch**
  - In `factory.js`, `case 'Frustum': mesh = createFrustum(ent)`.

- [x] **6.5 — register the renderer for HTML export**
  - In `py/pytanga/viz/export/_bootstrap/_html.py`, add
    `_RENDERERS_DIR / "frustum.js"` to `_RENDERER_FILES` (the single list that
    feeds both the HTML-export bootstrap and the CDN `js/tanga-viewer.js` bundle
    via `library_source_files()`).

- [x] **6.6 — bundle + tests**
  - Rebuild `js/tanga-viewer.js`; test serialization (apex and two-rect forms) and
    style passthrough through `to_dict`.

## Validation

`uv run pytest py/tests/viz/test_frustum.py -q && node --check py/pytanga/viz/templates/renderers/frustum.js && uv run python tools/build-viewer-js.py --check`

## Notes

- Keep the renderer wire format corner-based so the frontend does not re-derive
  the `Rectangle2D` in-plane basis (the Python serializer computes corners once).
- Follow the existing `rectangle2d.js` / `box.js` renderer conventions for
  outlines + optional translucent faces.

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this work
touches, so the new code aligns with the documented architecture. If this work
introduces or changes architecture, update the developer docs.
