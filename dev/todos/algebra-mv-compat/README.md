# Algebra MV cross-instance compatibility — Overview

**Created:** 2026-09-28 | **Status:** Done | **Branch:** `feat/algebra-mv-compat`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Let multivectors — and the layers built on them — combine across *different*
`Algebra` instances that have the same parameters, instead of only across the
identical instance. Today the raw `MV` arithmetic already works across
equal-parameter instances (both instances load the same cached compiled binding
module), but the higher layers (`BladeMask`, `Expression`, `tensor`, `solver`,
`matrix`) gate on object *identity* (`is`), so e.g. a `BladeMask` built from one
`BasisN3()` cannot be unioned with one built from a second `BasisN3()`.

Add an explicit `Algebra.compare()` member function plus `__eq__`/`__hash__`
that compare the algebra *parameters*, and switch every combinability check from
`is` identity to that equality. Any two `Algebra` instances with the same
`(dim, sig, dtype, modulus)` become interchangeable end to end.

## Architecture (short)

- The compile-time algebra identity is `(dim, sig, dtype)`; the value domain
  adds `modulus` (see `docs/dev/architecture/type-system-and-storage.md`). Two
  instances with the same tuple load the same compiled binding module
  (`py/pytanga/codegen/_cache.get_or_build`), so their `DynMV` objects are
  already compatible at the C++ level.
- `MV` arithmetic (`py/pytanga/algebra/_mv.py`) delegates to
  `self._alg._*_impl` and never checks the right operand's algebra; the result
  is bound to the *left* operand's algebra. This stays unchanged — it is the
  deliberate branch-free hot path
  (`dev/todos/algebra-hotpath-sdf-cylinder/02-operator-dispatch.md`).
- The identity checks live in `BladeMask`
  (`py/pytanga/blade_mask/_mask.py`, `predict.py`), `Expression`
  (`py/pytanga/expression/_expression.py`), `tensor`
  (`py/pytanga/tensor/ops.py`, `product.py`, `_labeled.py`), `matrix`
  (`py/pytanga/matrix/_product_data.py`), and `solver`
  (`py/pytanga/solver/solve.py`).

### Fixed contract (do not change across phases)

- `Algebra.compare(other) -> bool` — `True` iff `(dim, sig, dtype, modulus)` are
  all equal; `False` for any non-`Algebra`.
- `Algebra.__eq__(other) -> bool` — `NotImplemented` for non-`Algebra`, else
  `self.compare(other)`.
- `Algebra.__hash__() -> int` — `hash((dim, sig, dtype, modulus))`.
- Equality ignores `opns`, `precision`, `print_fmt`, the subclass
  `_swap_meet_join` flag, and cached named-blade `MV` attributes — none of these
  affect whether two MVs can be combined.
- All 19 combinability checks switch `is`/`is not` → `==`/`!=`; each site keeps
  its existing mechanism (`assert` stays `assert`, `raise` stays `raise`).
- `MV` operator dunders stay branch-free (no new per-call checks).
- `Algebra.embed()` keeps its `mv.algebra is self` guard (a "different *target*
  algebra" check, not a combinability check).
- Result MVs are still bound to the left operand's algebra.

## Decisions (confirmed)

- **Equality tuple = `(dim, sig, dtype, modulus)`** — `modulus` is included
  because two integer algebras with different moduli reduce differently and must
  not be interchangeable; `opns`/`precision`/`print_fmt`/`_swap_meet_join` are
  interpretation/display settings and are excluded.
- **`compare` + `__eq__`/`__hash__`** — `compare` is the explicit predicate;
  `__eq__`/`__hash__` make `==`, `in`, and dict/set keys work naturally.
- **Full propagation** — relax every `is` identity check across `BladeMask`,
  `Expression`, `tensor`, `solver`, `matrix` (scope confirmed by the user).
- **No hot-path guard** — do not add per-call compatibility checks to `MV`
  operators; the equal-parameter path already works, and a guard would regress
  the deliberate branch-free dispatch.
- **`embed()` unchanged** — keep `mv.algebra is self` (blade-relabeling target
  guard, unrelated to combinability).

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-algebra-equality.md](./01-algebra-equality.md) | Add `Algebra.compare`/`__eq__`/`__hash__` + tests |
| 2 | [02-blademask-compat.md](./02-blademask-compat.md) | Relax `BladeMask` (`_mask.py`, `predict.py`) identity checks + tests |
| 3 | [03-expression-compat.md](./03-expression-compat.md) | Relax `Expression` operand checks + tests |
| 4 | [04-tensor-solver-matrix-compat.md](./04-tensor-solver-matrix-compat.md) | Relax `tensor`/`solver`/`matrix` checks + tests |
| 5 | [05-docs-changelog.md](./05-docs-changelog.md) | Docs + branch changelog |

## Testing as you go

```bash
uv run pytest py/tests/algebra -q                                        # phase 1
uv run pytest py/tests/blade_mask -q                                     # phase 2
uv run pytest py/tests/expression -q                                     # phase 3
uv run pytest py/tests/tensor py/tests/solver py/tests/matrix -q         # phase 4
uv run ruff check py/pytanga/algebra py/pytanga/blade_mask \
    py/pytanga/expression py/pytanga/tensor py/pytanga/solver \
    py/pytanga/matrix                                                     # lint (each phase)
uv run ty check                                                          # type gate (phases 1-4)
uv run pytest -q                                                         # full suite (before PR)
```

## Non-goals

- No friendly error message for genuinely mismatched `MV` combination (the raw
  pybind11 `TypeError` remains; this plan only relaxes equal-parameter gating).
- No change to the `MV` hot-path dispatch or to `Algebra.embed()`.
- No change to the C++ binding, the generated code, or the `(dim, sig, dtype)`
  cache key.
- No `__hash__` on `BladeMask` (it stays unhashable, as today).
