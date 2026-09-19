# Phase 4 — N3 Euclidean projection example

## Goal

Add a runnable example that builds an N3 expression with `einf`/`eo` components
and projects it onto the Euclidean basis, then regenerate the example docs.

## Files

- New: `py/examples/ga/expression/project_onto_euclidean_n3.py`

## Steps

- [x] **4.1 — Write the example script**
  - Header per `dev/workflows/example-docs.md` (one-line `<name>.py — …`
    description, `Run with:` line, `Keywords:` line).
  - Use `BasisN3`, a full-mask `Variable`, and an `einf`/`eo`-inflected constant;
    build an `Expression`, then `Expression.project_onto` onto
    `BladeMask(alg, [alg.E1, alg.E2, alg.E3, alg.E12, alg.E13, alg.E23])`.
  - Print the before/after `out_mask` and evaluated values, and assert the result
    against the `MV.project_onto` reference so the example self-checks.

- [x] **4.2 — Regenerate example docs**
  - Run `uv run python tools/generate-example-docs.py` and confirm the check gate.

## Validation

`uv run python py/examples/ga/expression/project_onto_euclidean_n3.py && uv run python tools/generate-example-docs.py --check`

## Notes

- The Euclidean blade set in `BasisN3` is `e1, e2, e3, e12, e13, e23`
  (ids `1, 2, 4, 3, 5, 6`); `einf = ep + em` and `eo = 0.5·em − 0.5·ep` (ids
  `8` and `16`) are the terms the projection removes.

---

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.
