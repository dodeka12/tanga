# Phase 7 — `py/examples`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`, in particular
> `viz-architecture.md` for the viz examples) for the subsystem(s) this work
> touches, so the new code aligns with the documented architecture.  If this
> work introduces or changes architecture, update the developer docs.

## Goal

Annotate `py/examples` (78 untyped functions: `ga` 10, `viz` 68) so the example
scripts also pass the ANN + ty gates.

## Files

- Edit: `py/examples/ga/**/*.py`
- Edit: `py/examples/viz/**/*.py`

## Steps

- [x] **7.1 — `ga` examples (10)** — annotate the algebra/geometry demo scripts'
  `main`-style functions and local helpers (`-> None`, `-> MV`, `-> Point`, …).
- [x] **7.2 — `viz` examples (68)** — annotate the viz demo scripts' functions and
  `__init__` methods (`-> None`, `-> VizObjectRef`, …), following the same
  pattern as Phase 6.

- [x] **7.3 — Resolve `py/examples` ty diagnostics**
  - `uv run ty check py/examples` → 0 (baseline: measure in this phase).
  - Fix each (real bug / annotation inaccuracy) or add
    `# ty: ignore[<rule>]  # <reason>` for verified false positives.

## Validation

`uv run ruff check --select ANN --ignore ANN401 py/examples` → 0
`uv run ty check py/examples` → 0
`uv run python tools/generate-example-docs.py --check`

## Notes

- Per `dev/workflows/example-docs.md`, every example keeps its description +
  `Keywords:` docstring header intact — type hints only, no docstring changes.
- The `docs/py/examples/*.md` mirror is generated from the docstrings, so pure
  annotation additions must not change it; `generate-example-docs.py --check`
  confirms no drift.
- Some examples intentionally use `globals().update()` blade names (e.g.
  `ga/basis/basis_usage.py`) — those lines already carry `# type: ignore` /
  `noqa: F821`; leave them as-is.
