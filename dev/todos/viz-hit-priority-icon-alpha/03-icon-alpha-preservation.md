# Phase 3 — Preserve icon-point alpha through style updates and hover

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.
> Reference: `docs/dev/architecture/viz-architecture.md` (renderer/style
> pipeline, § "Surface material") and
> `docs/dev/architecture/viz-controls-and-interactions.md`
> (`## Interactive objects` — hover styling, `## Interaction surface`).

## Goal

A point whose alpha comes from a glyph texture (`IconPointStyle`, and any
`PointPath` drawing icons) must stay transparent after a style/selection update
and after a hover.  Fix: tag such materials once, and let every opacity writer
honour the tag.

## Files

- Edit: `py/pytanga/viz/templates/renderers/icon_point.js`
- Edit: `py/pytanga/viz/templates/renderers/utils.js`
- Edit: `py/pytanga/viz/templates/interaction.js`
- New: `py/tests/viz/test_icon_point_alpha.py`
- Regenerate: `js/tanga-viewer.js` (+ `js/tanga-viewer.manifest.json`)

## Steps

- [x] **3.1 — Tag the icon material (`renderers/icon_point.js`, lines 82-86)**
  - Inside `if (texture) { … }`, after `material.depthWrite = false;`:
    ```js
    // This material's alpha comes from the glyph texture, not from
    // `material.opacity`; tag it so opacity writers keep `transparent`
    // set and `depthWrite` off (see `applyOpacityUpdate`).
    material.userData = { ...(material.userData || {}), _alphaTexture: true };
    ```
  - No other renderer needs the tag: image planes and SDF surfaces already use
    the `uniforms.uOpacity` branch, which reads `_alphaTexture` today.

- [x] **3.2 — Generic opacity branch (`renderers/utils.js`, lines 350-362)**
  - Before `if (target !== undefined) {`, add
    `const alphaTex = !!(material.userData && material.userData._alphaTexture);`
  - Replace the two derived flags with the shared rule, mirroring the uniform
    branch above:
    ```js
    material.transparent = target < 1.0 || alphaTex;
    material.depthWrite = target >= 0.99 && !alphaTex;
    ```
  - Keep `material.opacity = target`, `needsUpdate = true`, and the fill-quad
    early-return untouched.

- [x] **3.3 — Hover (`interaction.js`, `_applyHover`, lines 271-286)**
  - In the `else if (m.opacity !== undefined)` branch of the opacity override:
    ```js
    m.opacity = opacity;
    const alphaTex = !!(m.userData && m.userData._alphaTexture);
    m.transparent = translucent || alphaTex;
    m.depthWrite = !translucent && !alphaTex;
    ```
  - Leave the `usesUniformOpacity` branch alone (it deliberately keeps
    `depthWrite` for SDF depth) and leave `_resetHover` alone — it restores the
    saved `transparent`/`depthWrite` from `_saveMeshState`, which now captures
    the corrected (transparent, no-depth-write) values.

- [x] **3.4 — Regression test (`py/tests/viz/test_icon_point_alpha.py`)**
  - Docstring: why the tag exists (a style update with canonical
    `opacity: 1.0` used to make the icon quad opaque).
  - Source-level asserts using
    `Path(__file__).resolve().parents[3]` for the repo root:
    - `templates/renderers/icon_point.js` sets `_alphaTexture: true` inside the
      `if (texture)` block;
    - `templates/renderers/utils.js` contains `target < 1.0 || alphaTex` and
      `target >= 0.99 && !alphaTex` **twice** (uniform + generic branch);
    - `templates/interaction.js` contains `translucent || alphaTex` and
      `!translucent && !alphaTex`.
  - Bundle asserts with `from pytanga.viz.export._bootstrap import generate_library_js`:
    - the generated library contains `_alphaTexture` at least twice (icon
      marker + `applyOpacityUpdate`);
    - the committed `js/tanga-viewer.js` contains `_alphaTexture` (bundle was
      rebuilt).

- [x] **3.5 — Rebuild the export bundle**
  - `uv run python tools/build-viewer-js.py --force`, then confirm
    `git status --short js/` shows **both** `js/tanga-viewer.js` and
    `js/tanga-viewer.manifest.json`, and that the diff only touches the icon
    marker + `applyOpacityUpdate` regions.
  - `uv run python tools/build-viewer-js.py --check` must pass (the test in
    3.4 asserts the committed content, so an un-rebuilt bundle fails CI).

## Validation

```bash
uv run pytest py/tests/viz/test_icon_point_alpha.py py/tests/viz/test_export_renderers.py -q && uv run python tools/build-viewer-js.py --check
```

## Notes

- `utils.js` and `icon_point.js` **are** in `_RENDERER_FILES`
  (`export/_bootstrap/_html.py`), hence the mandatory rebuild.  `interaction.js`
  is live-viewer only and must not appear in the bundle diff.
- The `_alphaTexture` name is already used by the uniform branch, so the tag is
  a naming continuation, not a new concept.
- Hover may legitimately *change* `material.opacity`; the rule only decides
  `transparent`/`depthWrite`, so a hover-opacity animation still works while the
  glyph stays cut out.
