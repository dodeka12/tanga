# Phase 2 — Hoist the per-call modulus branch out of `Algebra` operators

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Remove the per-call `if self._modulus is not None` re-check from the `MV`
operator hot path (report `_input/pytanga-mv-operator-dispatch-overhead.md`).
Branch-free implementations are bound once in `Algebra.__init__` under private
names (`_add_impl`, `_gp_impl`, …), and the `MV` dunders / named-GA methods call
those directly instead of going through `Algebra.add/sub/scale/gp/op/ip`.
Results are unchanged; the public `Algebra` methods are kept (with the branch)
for direct callers that are not on the hot path.

## Files

- Edit: `py/pytanga/algebra/_algebra.py`
- Edit: `py/pytanga/algebra/_mv.py`
- New: `py/tests/algebra/test_operator_dispatch.py`
- Edit: `py/tests/test_modular.py`

## Steps

- [x] **2.1 — Add private plain/modular implementations**
  - In `Algebra`, add twelve annotated private methods (keep the existing public
    methods' docstrings as the semantic reference):
    - `_add_plain(a, b)`, `_add_modular(a, b)`
    - `_sub_plain(a, b)`, `_sub_modular(a, b)`
    - `_scale_plain(a, s)`, `_scale_modular(a, s)`
    - `_gp_plain(a, b)`, `_gp_modular(a, b)`
    - `_op_plain(a, b)`, `_op_modular(a, b)`
    - `_ip_plain(a, b)`, `_ip_modular(a, b)`
  - Plain variants: `return MV(self._mod.<op>(a._impl, b._impl), self)`.
  - Modular variants:
    - `add`/`sub`/`scale`: `return self.reduce(MV(self._mod.<op>(a._impl, …),
      self), self._modulus)`.
    - `gp`/`op`/`ip`: `return self.gp_mod(a, b, self._modulus)` (reuse the
      existing public `*_mod` methods, which already guard dtype).

- [x] **2.2 — Bind private impls and route the `MV` dunders through them**
  - In `Algebra`, declare the six impl attributes at class level (typing Rule 5):
    `_add_impl`/`_sub_impl`/`_gp_impl`/`_op_impl`/`_ip_impl` as
    `Callable[[MV, MV], MV]`, and `_scale_impl` as `Callable[[MV, float], MV]`.
  - At the end of `Algebra.__init__`, bind them to the plain or modular variants
    based on `modulus is None` (private names, so no public-method shadowing).
  - In `MV` (`py/pytanga/algebra/_mv.py`), change the six operator dunders and the
    `MV.gp`/`MV.op`/`MV.ip` named methods to call `self._alg._<op>_impl(...)`
    instead of `self._alg.<op>(...)` (15 call sites). The public
    `Algebra.add/sub/scale/gp/op/ip` methods are kept unchanged for direct callers.

- [x] **2.3 — Tests (correctness equivalence)**
  - New `py/tests/algebra/test_operator_dispatch.py`: on a `BasisE3()` (float,
    non-modular), assert `a + b`, `a - b`, `2 * a`, `a * b`, `a ^ b`, `a | b`
    equal their expected values (results identical to before the change).
  - Extend `py/tests/test_modular.py`: on
    `Algebra(dim=3, sig=0, dtype="int64", modulus=MODULUS)`, assert `a + b`,
    `a * b`, `a ^ b` still reduce modulo `MODULUS` (compare against the explicit
    `reduce(...)` result).
  - Annotate all new test functions with `-> None`.

- [x] **2.4 — Type/lint gates**
  - Run `uv run ty check` and `uv run ruff check .`. Confirm no *new* `ty`
    diagnostics are introduced by the private-impl binding (the only `ty`
    diagnostics on this branch are the two pre-existing `_image_wire.py`
    `codec` warnings, unrelated to this work). Resolve any new diagnostic per
    `docs/dev/architecture/typing-and-annotations.md` Rule 7 — do not weaken the
    gate.

## Validation

```
uv run pytest py/tests/algebra/test_operator_dispatch.py py/tests/test_modular.py -q
uv run ty check
uv run ruff check py/pytanga/algebra/_algebra.py
```

## Notes

- The public `Algebra.add/sub/scale/gp/op/ip` methods still carry the
  `self._modulus is not None` branch and remain for direct callers (e.g.
  `_display_basis._op_chain`); only the `MV` hot path skips it via the bound
  private impls.
- `self._modulus` is assigned exactly once in `__init__`; the bindings read it
  only at construction, so they stay correct for the instance's lifetime.
- `neg`, `rev`, `conj`, and `inv` have no per-call `self._modulus is not None`
  branch in the same pattern, so they are left unchanged.
