# Phase 1 — `Algebra.compare` / `__eq__` / `__hash__`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Add an explicit algebra-equality API to `Algebra` — `compare()`, `__eq__`, and
`__hash__` — all based on the parameter tuple `(dim, sig, dtype, modulus)`. This
is the fixed contract every later phase builds on.

## Files

- Edit: `py/pytanga/algebra/_algebra.py`
- New: `py/tests/algebra/test_algebra_compare.py`

## Steps

- [ ] **1.1 — Add the equality methods**
  - In `Algebra` (near the `modulus` property, alongside the other properties),
    add three annotated methods:
    - `compare(self, other: "Algebra") -> bool` — return `False` unless
      `isinstance(other, Algebra)`, then compare `self._dim`, `self._sig`,
      `self._dtype`, and `self._modulus` to `other`'s.
    - `__eq__(self, other: object) -> bool` — return `NotImplemented` for
      non-`Algebra`, else `self.compare(other)`.
    - `__hash__(self) -> int` — `return hash((self._dim, self._sig, self._dtype,
      self._modulus))`.
  - Document on `compare` that `opns`, `precision`, `print_fmt`, and subclass
    interpretation (`_swap_meet_join`) are intentionally **not** compared, since
    they do not affect whether two MVs can be combined.
  - Follow `docs/dev/architecture/typing-and-annotations.md` (annotate all
    three; no `Any`).

- [ ] **1.2 — Tests**
  - New `py/tests/algebra/test_algebra_compare.py`, all test functions annotated
    `-> None`:
    - `BasisN3() == BasisN3()` is `True`; `BasisN3() == BasisE3()` is `False`.
    - `BasisN3().compare(BasisN3())` is `True`; `.compare(BasisE3())` is
      `False`; `.compare("x")` is `False` (non-algebra).
    - `hash(a) == hash(b)` when `a == b` (two `BasisN3()` instances).
    - `Algebra(3, 0, "int64") != Algebra(3, 0, "int64", modulus=7)` (modulus
      differs); `Algebra(3, 0, "int64", modulus=7) == Algebra(3, 0, "int64",
      modulus=7)`.
    - `BasisN3(opns=True) == BasisN3(opns=False)` is `True` (opns excluded).
    - MVs from two `BasisN3()` instances combine: `a.multivector({1: 1.0}) +
      b.multivector({2: 2.0})` equals `a.multivector({1: 1.0, 2: 2.0})`, and the
      result's `.algebra is a` (left operand wins).

## Validation

```
uv run pytest py/tests/algebra/test_algebra_compare.py -q
uv run ruff check py/pytanga/algebra/_algebra.py
uv run ty check
```

## Notes

- `_dim`/`_sig`/`_dtype`/`_modulus` are assigned once in `__init__` and never
  reassigned, so `__hash__` is stable for an instance's lifetime.
- Defining `__eq__` without `__hash__` would make `Algebra` unhashable — hence
  the explicit `__hash__`.
