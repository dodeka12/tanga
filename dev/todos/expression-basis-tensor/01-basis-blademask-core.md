# Phase 1 — `BladeMask` named basis

## Goal

Teach `BladeMask` to carry an optional named basis directly (an ordered tuple of
``(name, MV)`` directions, `_basis: tuple[tuple[str, MV], ...] | None`),
auto-attach the algebra display basis on construction, expose `basis_vectors` /
`basis_names` / `with_basis` / `basis_matrix`, and fix string parsing so composed
names (`einf`, `eo`) expand to raw ids.  No separate `Basis` type.

## Files

- Edit: `py/pytanga/blade_mask/_mask.py`
- Edit: `py/tests/blade_mask/test_named_basis.py`

## Steps

- [x] **1.1 — `BladeMask` named-basis storage + accessors**
  - Add `_basis: tuple[tuple[str, MV], ...] | None` to `BladeMask.__slots__`
    (default `None`).
  - Add `basis_vectors` (the direction MVs, falling back to raw blades in `ids`
    order) and `basis_names` (the names, falling back to raw blade names).
  - Keep `ids`, `index`, `names()`, `__len__`, `__iter__`, `__contains__`,
    `__eq__`, `__repr__` unchanged (raw identity).

- [x] **1.2 — `with_basis` and `basis_matrix`**
  - `with_basis(directions, *, names=None) -> BladeMask`: accept
    `Sequence[MV]` or `Sequence[tuple[str, MV]]`; validate every direction's
    non-zero raw ids ⊆ `self._ids`; return a new mask over the same raw ids with
    the directions attached (as a tuple).
  - `basis_matrix(directions=None) -> np.ndarray`: resolve directions to MVs
    (default `self.basis_vectors`) and return
    `to_matrix(mvs, mask=self).data` — shape `(len(self), n_directions)`.

- [x] **1.3 — auto-attach algebra display basis**
  - In `BladeMask.__init__`, after resolving `raw`, call a private helper that
    reads `alg._get_display_basis()` (already exists) and, *iff* the entries
    whose support ⊆ `raw` have supports whose union == `raw`, sets `_basis` to
    those `(name, blade)` entries (as a tuple).  Otherwise `_basis = None`.
  - Applies to every constructor path (`Algebra`, `MV`, `list[MV]`, `from_mv`,
    `from_array`, `full`) so `mask_for(Rotor)` etc. pick up default names too.

- [x] **1.4 — composed-name string parsing**
  - Factor the composite `named_basis` build out of `Algebra.multivector` into a
    reusable `Algebra` helper (`_composite_basis()`), extend the MV string parser
    to match alphabetic blade names, and pass the named basis in `BladeMask`'s
    `_parse_mv_string(...)` calls so `BladeMask(N3, "e1 + einf")` resolves
    `einf` → raw `{8, 16}` (and `eo`).

- [x] **1.5 — tests**
  - `basis_names`/`basis_vectors` raw fallback (ids order, names in ids order).
  - `with_basis` reduced set (6 directions over 9 twist ids) + out-of-mask
    direction raises.
  - `basis_matrix` columns for `einf`/`eo` over N3 grade-1 mask.
  - Auto display basis: `BladeMask(N3, grades=[1])` → `e1,e2,e3,einf,eo`;
    `BladeMask(N3, "e4")` → raw-only (raw name `e4`).
  - String parse: `BladeMask(N3, "e1 + einf").ids == [1, 8, 16]`.

## Validation

`uv run pytest py/tests/blade_mask/ -q`

## Notes

- Do not change `BladeMask.names()` (grade-sorted display) — `basis_names()` is a
  separate, ids-ordered accessor.

---

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

