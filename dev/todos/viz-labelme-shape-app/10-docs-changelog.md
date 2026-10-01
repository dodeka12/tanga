# Phase 10 — Docs, dev-docs, tests, changelog

## Goal

Finalize: update entity/active-element docs, the developer docs (only where a
contract changed), run the full validation gate, and record the changelog.

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` and `docs/dev/architecture/`; if any prior phase introduced or
> changed a documented contract, update the developer docs here (per
> `dev/workflows/changelog.md` / `dev/workflows/pull-request.md`).

## Files

- Edit: `docs/py/viz/entities/active-elements/*.md` (add `ActCircle`, `ActLine`;
  update `ActRectangle2D` rotation, `ActPolygon` insert/delete)
- Edit: `docs/py/viz/entities/entities/*.md` or styles doc (add
  `CirclePointStyle`, `IconPointStyle`)
- New: `docs/py/viz/entities/labelme.md` (or similar) for the labelme module
- Edit: `docs/changelog/2026/09/28_feat-more-act-entities.md` (append this work)
- Edit: `docs/dev/architecture/viz-controls-and-interactions.md` / `viz-architecture.md`
  (only if a contract changed — e.g. new point-style variants are a doc-worthy
  extension recipe note)

## Steps

- [x] **10.1 — Active-element docs**
  - Document `ActCircle` (center + radius), `ActLine` (open polyline), the new
    `ActRectangle2D` `angle`/`min_size`, and `ActPolygon`'s insert-after /
    delete-any-vertex behavior.
- [x] **10.2 — Style docs**
  - Document `CirclePointStyle` / `IconPointStyle` next to `CrossHairPointStyle` /
    `SquarePointStyle`.
- [x] **10.3 — labelme module docs**
  - A short reference page for `pytanga.viz.labelme` (dataclasses, store,
    `add_shapes`, `allow_extensions`).
- [x] **10.4 — Developer docs**
  - Update `viz-controls-and-interactions.md`'s interactive-objects/extension
    recipe if the new point styles or composites warrant a mention; otherwise
    leave as-is (note the decision).
- [x] **10.5 — Changelog**
  - Append the new features/fixes to the branch changelog
    `docs/changelog/2026/09/28_feat-more-act-entities.md` (per
    `dev/workflows/changelog.md`).
- [x] **10.6 — Full validation gate**
  - Run the README "Testing as you go" final set.

## Validation

```
uv run pytest -q
uv run ruff check .
uv run ty check
node --test 'js/dev/tests/*.test.mjs'
node js/dev/tests/check-syntax.mjs
uv run python tools/generate-example-docs.py --check
uv run mkdocs build --strict
```

## Notes

- This is the final phase; flip the `README.md` `Status:` to `Done` after the
  gate passes.
