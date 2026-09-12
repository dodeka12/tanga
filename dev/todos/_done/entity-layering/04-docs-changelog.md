# Phase 4 — Developer docs, changelog, full regression

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Document the new module layering, write the changelog entry, and run the full
suite to confirm the refactor is complete and backward compatible.

## Files

- New: `docs/dev/architecture/geometry-module-layering.md` (or extend an existing geometry doc)
- New: `docs/changelog/<date>_refactor-entity-layering.md` (see `dev/workflows/changelog.md`)
- Edit: `dev/todos/entity-layering/README.md` (flip `Status:` to `Done`)

## Steps

- [x] **4.1 — Document the layering**
  - Add `docs/dev/architecture/geometry-module-layering.md` describing the
    `pytanga.entity → pytanga.quadric → pytanga.geometry → pytanga.viz` DAG, the
    `Vec3`/`Point`/`Direction` relationship, the `Refinable` protocol, and the
    re-export-shim compatibility contract.
  - Link it from any existing index/README under `docs/dev/architecture/`.

- [x] **4.2 — Changelog**
  - Write a changelog entry per `dev/workflows/changelog.md` covering: new
    `pytanga.entity` leaf (`Vec3`, `Point`, `Direction`, `Refinable`), the
    `Conic`/`Quadric3D` move to `pytanga.quadric`, and the duck-typed
    `geometry.refine`.

- [x] **4.3 — Full regression**
  - `uv run pytest -q` (or the project's full test command) passes.

- [x] **4.4 — Wrap up**
  - Update this README's `Status:` line to `Done`.
  - PR deferred: both plans will be PR'd together after implementation.

## Validation

```
uv run pytest -q
uv run grep -rn "pytanga.geometry" py/pytanga/quadric/ || echo "clean: no geometry imports in quadric"
```

## Notes

- PR/changelog hash rename deferred until both plans are implemented (single PR).
