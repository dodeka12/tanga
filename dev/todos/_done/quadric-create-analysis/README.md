# Quadric Create + Analysis Consolidation — Overview

**Created:** 2026-09-12 | **Status:** Done | **Branch:** `refactor/quadric-create-analysis`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`, in particular
> `geometry-module-layering.md`) for the subsystem(s) this work touches, so the
> new code aligns with the documented architecture.  If this work introduces or
> changes architecture, update the developer docs.

## Goal

Make `pytanga.quadric` the single owner of quadric-space math by moving the Q2
(2D conic) and Q3 (3D quadric) entity→MV **creation** and MV→entity **analysis**
out of `pytanga.geometry` into `pytanga.quadric`.  `pytanga.geometry` keeps thin
re-export shims, so the public API and all existing behavior are unchanged.

## Architecture (short)

- `pytanga.quadric` gains three modules (one per concern, both dimensions, like
  the existing `_basis` / `_embedding` / `_mapping`):
  - `_create.py` — entity → MV: the conic/quadric symmetric-matrix construction,
    point embedding, and the conic-space rotation rotor (Perwass).
  - `_analysis.py` — MV → entity: grade dispatch to `Conic` / `Quadric3D` /
    `Point` / `PointSet`.
  - `_pointset.py` — point recovery from quadric blades + `two_conic_intersection`
    (moved from `geometry/_pointset.py`).
- `pytanga.geometry` keeps:
  - `create_q2.py` / `create_q3.py` → shims re-exporting `quadric._create`.
  - `analysis_q2.py` / `analysis_q3.py` → shims re-exporting `quadric._analysis`.
  - `_pointset.py` → shim for `two_conic_intersection` (still public API).
- The layering DAG is preserved: `quadric` imports `geometry.entities` **lazily**
  (the `_entities()` pattern already used by `quadric/refine.py`), so the
  `quadric ↔ geometry.entities` import cycle never fires at import time.

## Decisions (confirmed)

- `quadric` owns entity→MV creation **and** MV→entity analysis (not just the rotor).
- One module per concern, both dims (matches `_basis` / `_embedding` / `_mapping`).
- The generic entry points (`create_entity` / `create_point` / `create_rotor`,
  `analyze_entity`) dispatch on `basis.dim` / `mv.algebra.dim`.
- `geometry` keeps thin shims; public API unchanged; no behavior change.
- No PR — deferred until after this plan (single PR with the prior quadric work).

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-create-to-quadric.md](./01-create-to-quadric.md) | Move Q2/Q3 entity→MV creation into `quadric/_create.py` |
| 2 | [02-analysis-to-quadric.md](./02-analysis-to-quadric.md) | Move Q2/Q3 MV→entity analysis + point recovery into `quadric/_analysis.py` / `_pointset.py` |
| 3 | [03-docs-changelog.md](./03-docs-changelog.md) | Update layering doc + changelog + full regression |

## Testing as you go

- `uv run pytest py/tests/geometry -q` (per phase)
- `uv run pytest -q` (full, final phase)
- `uv run mkdocs build --strict` (final phase)

## Non-goals

- No behavior change (pure relocation; existing tests must stay green).
- No new entities, operators, or algebras.
- No changes to `pytanga.viz` or the frontend.
- No PR / changelog hash rename (deferred).
