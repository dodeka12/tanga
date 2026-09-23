# Phase 1 — GA sequence products (`op`, `join`, `meet`, `gp`)

## Goal

Module-level reducers in `pytanga.algebra` that compute the outer product, join,
meet, and geometric product over a **sequence** of multivectors (today only the
binary `Algebra.*` / `MV.*` forms exist).

## Files

- New: `py/pytanga/algebra/_reduce.py`
- Edit: `py/pytanga/algebra/__init__.py` (import + `__all__`)
- New: `py/tests/algebra/test_reduce.py`

## Steps

- [x] **1.1 — `_reduce.py`**
  - `op`, `join`, `meet`, `gp`, each `(mvs: Sequence[MV]) -> MV`.
  - Left-fold via `MV.op` / `MV.join` / `MV.meet` / `MV.gp`; empty → `ValueError`,
    length-1 → returned unchanged.

- [x] **1.2 — export**
  - Import the four functions and add them to `__all__` in
    `py/pytanga/algebra/__init__.py`.

- [x] **1.3 — tests** (`py/tests/algebra/test_reduce.py`)
  - Empty sequence raises; single MV passes through; 2- and 3-element sequences
    equal the manual binary reductions (`m1 ^ m2 ^ m3`, `m1.join(m2).join(m3)`, …).

## Validation

`uv run pytest py/tests/algebra/test_reduce.py -q`

## Notes

- This is a thin reducer over existing `MV` methods — no new algebra.
- `quadric3d_demo.py` currently hand-rolls `functools.reduce(lambda a, c: a.join(c),
  points)`; phase 4 replaces that with `join(...)`.

---

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this work
> touches, so the new code aligns with the documented architecture. If this work
> introduces or changes architecture, update the developer docs.
