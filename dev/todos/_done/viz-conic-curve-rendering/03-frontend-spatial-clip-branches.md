# Phase 3 — Spatial clipping + both hyperbola branches (frontend)

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture. If this
> work introduces or changes architecture, update the developer docs.

## Goal

Draw the conic curves bounded to a sensible spatial size (backend `extent`),
and draw **both** hyperbola branches.

## Files

- Edit: `py/pytanga/viz/templates/renderers/hyperbola.js`
- Edit: `py/pytanga/viz/templates/renderers/parabola.js`

## Steps

- [x] **3.1 — Hyperbola: both branches, spatially clipped.**
  - Read `extent = styleParam(ent, 'extent', 5.0)` as a spatial half-size.
  - Sample `t ∈ [-t_max, t_max]` with
    `t_max = min(acosh(extent / a), asinh(extent / b))` (guarded so the
    arguments are `≥ 1` / finite).
  - Emit **both** branches: `center + d1·(±a·cosh t) + d2·(b·sinh t)`.
- [x] **3.2 — Parabola: spatially clipped.**
  - Read `extent = styleParam(ent, 'extent', 5.0)`.
  - Sample `t ∈ [-t_max, t_max]` with `t_max = min(extent, sqrt(2 · p · extent))`,
    keeping the full symmetric two-arm sampling `vertex + dir·(t²/(2p)) +
    dPerp·t`.
- [x] **3.3 — Tests.**
  - `node --check` both files; run the export-renderers lockstep test.

## Validation

`node --check py/pytanga/viz/templates/renderers/hyperbola.js py/pytanga/viz/templates/renderers/parabola.js && uv run pytest py/tests/viz/test_export_renderers.py -q`

## Notes

- `extent` is a **spatial half-size** (matching `PlaneStyle.extent` /
  `SpaceStyle.extent`), not the old parameter range. The backend default is set
  in Phase 1; the `5.0` fallback here is only a safety net.
