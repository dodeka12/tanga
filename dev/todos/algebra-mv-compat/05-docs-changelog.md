# Phase 5 — Docs + changelog

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Document the new algebra-equality behavior and record the change in the branch
changelog.

## Files

- Edit: `docs/py/ga/algebra/algebra.md`
- New/Edit: branch changelog under `docs/changelog/2026/09/` (per
  `dev/workflows/changelog.md`)

## Steps

- [ ] **5.1 — Changelog**
  - Add a `## New Features` bullet to the branch changelog describing
    cross-instance MV compatibility and the `Algebra.compare`/`__eq__` API
    (follow `dev/workflows/changelog.md` for the file name and
    since-relative title).

- [ ] **5.2 — Docs**
  - In `docs/py/ga/algebra/algebra.md`, add a short paragraph: `compare()` /
    `__eq__` compare `(dim, sig, dtype, modulus)`; `opns`, `precision`, and
    display settings are excluded; equal-parameter instances are
    interchangeable across `MV`, `BladeMask`, `Expression`, `tensor`, `solver`,
    and `matrix`.

- [ ] **5.3 — Final validation**
  - `uv run pytest -q` (full suite), `uv run ty check`, `uv run ruff check .`.
  - Confirm no pre-existing behavior changed beyond the intended
    equal-parameter relaxation.

## Validation

```
uv run pytest -q
uv run ty check
uv run ruff check .
```

## Notes

- If the changelog file is renamed to the squashed-commit hash at PR time,
  follow `dev/workflows/pull-request.md`.
- No developer-doc architecture changes are introduced by this work (the
  compile-time `(dim, sig, dtype)` shape and value-domain `modulus` model are
  already documented in `docs/dev/architecture/type-system-and-storage.md`);
  only the user-facing `algebra.md` reference is updated.
