# Quadric-space rotation rotor (Q2 + Q3) — Overview

**Created:** 2026-09-12 | **Status:** Done | **Branch:** `feat/quadric-space`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`, in particular
> `geometry-module-layering.md` and `viz-architecture.md`) for the subsystem(s)
> this work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Extend the quadric-space rotor from the 2D conic space (Q2, already present) to
the 3D quadric space (Q3), document the full Perwass-style derivation, add
MV→operator analysis (`Rotor(angle, axis)`) for both Q2 and Q3, and add a
3D `quadric3d_demo.py` plus "effective rotor" visualization to both demos.

## Architecture (short)

- **`quadric/_create.py`** — `create_rotor(basis, angle, axis)` gains the Q3
  branch: a rotation about an *arbitrary* axis, built as the product of three
  commuting factors `R_lin · R_mixed · R_quad` (linear at rate θ, mixed quadratic
  at rate θ, traceless quadratic at rate 2θ).
- **`quadric/_analysis.py`** — new `analyze_rotor` / `analyze_operator` for Q2 and
  Q3, returning the existing `pytanga.geometry.operators.Rotor` (angle + axis;
  axis = `Dir(0,0,1)` for Q2).  Imported lazily to preserve the
  `quadric ↔ geometry` layering.
- **`geometry/analysis.py`** — `analyze_operator` dispatcher routes `"q2"`/`"q3"`
  to the `analysis_q2`/`analysis_q3` shims (which re-export
  `quadric._analysis.analyze_operator`).
- **Demos** — `conic_demo.py` (2D, one angle slider) and new
  `quadric3d_demo.py` (3D, three sliders: two spherical angles for the axis +
  one rotation angle).  Both reconstruct the conic/quadric from points, rotate
  it, and visualize the **effective rotor** via `viz.add(Rotor(angle, axis))`
  (existing operator renderer).
- **`dev/notes/quadric-rotor-derivation.md`** — the derivation with a copyright +
  author notice.

## Decisions (confirmed)

- **Three sliders = axis (2 spherical angles) + rotation angle (1)** (confirmed by
  the user).  The effective rotor is a single rotation about a user-chosen axis.
- **Rotor analysis returns the existing `Rotor(angle, axis)` dataclass**
  (`geometry.operators`), matching `create_rotor`'s input and the viz operator
  renderer; Q2 always returns axis `Dir(0,0,1)`.
- **Q3 `create_rotor` supports an arbitrary axis** (full SO(3)), via the
  three-factor product below (numerically verified against matrix rotation).
- **9 points / 3 action points.**  A 3D quadric has 9 dof (10 homogeneous
  coefficients up to scale); 9 points in general position give 9 independent
  constraints → a unique quadric.  Dragging 3 of the 9 points (3×3 = 9 dof)
  therefore reaches a full-dimensional open set of quadrics — every
  non-degenerate quadric up to a measure-zero set (degenerate plane/pair/
  imaginary quadrics are not reachable).  This is recorded in the demo docstring.
- **Effective rotor visualization reuses the existing operator renderer**
  (`viz.add(Rotor(angle, axis))` → axis + arc); no new frontend work.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-derivation-doc.md](./01-derivation-doc.md) | Write `dev/notes/quadric-rotor-derivation.md` (Q2 + Q3 + analysis) |
| 2 | [02-create-rotor-q3.md](./02-create-rotor-q3.md) | Implement Q3 `create_rotor` (arbitrary axis) |
| 3 | [03-analyze-rotor-q2-q3.md](./03-analyze-rotor-q2-q3.md) | Add `analyze_rotor`/`analyze_operator` for Q2 + Q3 and wire the dispatcher |
| 4 | [04-demos.md](./04-demos.md) | `quadric3d_demo.py` + effective-rotor viz in both demos |
| 5 | [05-docs-changelog.md](./05-docs-changelog.md) | Layering doc, changelog, example-docs regen, full regression |

## Testing as you go

- `uv run pytest py/tests/geometry -q` (phases 2–3)
- `uv run pytest py/tests/geometry/test_conic_create.py py/tests/geometry/test_conic_analysis.py -q`
- `uv run python -m py_compile py/examples/ga/quadric/quadric3d_demo.py` (phase 4)
- `uv run python tools/generate-example-docs.py --check` (phase 4–5)
- `uv run pytest -q` + `uv run mkdocs build --strict` (phase 5)

## Non-goals

- No translator / dilator / reflection operators in the quadric spaces (only the
  rotation rotor — those don't exist in `CA{6}`/`CA{10}`).
- No new frontend renderer (the rotor reuses the existing operator renderer).
- No PR / changelog hash rename (deferred to the combined quadric PR).
- No change to the Q2 rotor formula (it already matches Perwass).
