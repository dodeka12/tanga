# Phase 8 — Docs + examples + changelog

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` and re-verify the architecture docs are consistent with the code
> after Phases 1-7 (Phase 5 already updated the two viz docs; re-check them).

## Goal

Finalize the user-facing docs, the example apps, and the branch changelog; run
the full validation.

## Files

- Edit: `py/examples/apps/calibrated_labeling_app.py`
- Edit: `py/examples/apps/image_labeling_app.py`
- Edit: `docs/py/viz/…` (any entity/labelme pages that document
  `Rectangle2D`/`Ellipse`/`Circle` or `LabelMeStore` — update signatures/fields)
- Edit: `docs/changelog/YYYY/MM/<DD>_fix-rectangle2d.md` (new)
- Edit: `dev/todos/viz-shape-plane-basis/README.md` (`Status:` → `Done`)

## Steps

- [x] **8.1 — Developer docs re-check.**
  - Re-read `viz-architecture.md` and `viz-controls-and-interactions.md` and make
    any remaining wording consistent with `pixel_axes()`, the `Rectangle2D.dir_u/
    dir_v` + `Ellipse.angle` fields, and the new ellipse labelme form.

- [x] **8.2 — Example apps `_act_from_entity`.**
  - In both labeling apps, the `Ellipse` branch must add the entity's scalar
    rotation to the basis angle: `angle = atan2(du·v0, du·u0) + entity.angle`
    (with `du = entity.dir_u or u0`), since `dir_u` is now the basis, not the
    semi-axis.

- [x] **8.3 — User-facing docs.**
  - Update entity/labelme pages that show `Rectangle2D`/`Ellipse` constructors or
    labelme shape examples (new `dir_u`/`dir_v`/`angle`; ellipse scalar form).

- [x] **8.4 — Changelog.**
  - Run `uv run python tools/last-release.py` for the `# Changes since version …`
    title (do not guess the version).
  - Create `docs/changelog/YYYY/MM/DD_fix-rectangle2d.md` (branch form; date =
    branch start) with `## Bug Fixes` for the two findings and `## New Features`
    for the ellipse scalar storage — follow `dev/workflows/changelog.md`.

- [x] **8.5 — Final validation.**
  - Run the full suite and lint (see Validation).

## Validation

`uv run pytest py/tests/viz -q && uv run pytest py/tests/geometry -q && uv run ruff check . && uv run ty check && uv run mkdocs build --strict`

## Notes

- The changelog index update (`docs/changelog/index.md`) is done at PR time
  (after the hash rename), not here — see `dev/workflows/changelog.md`.
- Mark this phase's steps `- [x]` only after each passes its gate.
