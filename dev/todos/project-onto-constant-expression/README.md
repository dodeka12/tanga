# `project_onto` + constant `Expression` — Overview

**Created:** 2026-09-02 | **Status:** Done | **Branch:** `fix/expressions`

## Goal

Implement the two changes requested in `_input/more-fixes.md`:

1. Replace the confusing `project_to` with `project_onto`, fixing the direction
   at the C++ level as well as the Python level.
2. Add constant-multivector expressions: `Expression(A)` and
   `Expression(A, BladeMask)`.

## Background

- `MV.project_to` / `Algebra.project_to` currently have inconsistent semantics.
  The `MV` branch calls the C++ `Tan::GA::ProjectTo` (in
  `cpp/Tan.GA/MV_Operators.h:806`), which zeroes `a` and copies **`b`'s**
  coefficient at each of **`a`'s** blades — i.e. it returns `b` projected onto
  `a`, the opposite of the docstring. The `int`/`list[int]` branches (in
  `py/pytanga/algebra/_algebra.py:724-743`) do the opposite (restrict `a`).
- `Expression.__init__` (`py/pytanga/expression/_expression.py:41`) only accepts
  an `MVLabeledTensor`; a constant expression is built internally by
  `_to_expression`, but there is no public `Expression(A)` path.

## Decisions (confirmed)

- Remove `project_to` everywhere (breaking change) and add `project_onto`.
- `a.project_onto(b)` returns **`a`'s** components:
  - `b: MV` — keep `a`'s blades where `b` has a non-zero coefficient.
  - `b: BladeMask` — keep `a`'s blades whose id is **exactly** in `b.ids`
    (exact membership, not subset/bitmask semantics).
- Fix the C++ implementation too: replace `ProjectTo`/`ProjectToBlade` with a
  correctly-directed `ProjectOnto` (MV overload) and a `ProjectOnto` overload
  taking `GA::CBladeMask` (exact blade-id membership via `Contains`).
- `Expression(A)` → constant expression whose output mask is `BladeMask(A)`
  (non-zero blades). `Expression(A, BladeMask)` → constant expression whose
  output mask is the given mask (blades of `A` outside the mask are dropped).

### Fixed contract

```python
# Algebra / MV
a.project_onto(b) -> MV            # b: MV | BladeMask

# Expression
Expression(A)                      # constant, out_mask = BladeMask(A)
Expression(A, mask)                # constant, out_mask = mask (BladeMask)
```

```cpp
// cpp/Tan.GA/MV_Operators.h
template <typename TMultivectorA, typename TMultivectorB>
void ProjectOnto(TMultivectorA& wA, const TMultivectorB& wB);
// keep wA's coeffs where wB.GetValueBlade(...) is true

template <typename TMultivectorA>
void ProjectOnto(TMultivectorA& wA,
                 const GA::CBladeMask<typename TMultivectorA::TBlade>& xMask);
// keep wA's coeffs where xMask.Contains(blade)
```

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-cpp-codegen-project-onto.md](./01-cpp-codegen-project-onto.md) | Add C++ `ProjectOnto` + codegen bindings (additive). |
| 2 | [02-python-project-onto-remove-project-to.md](./02-python-project-onto-remove-project-to.md) | Add Python `project_onto`, remove `project_to`, tests. |
| 3 | [03-constant-expression.md](./03-constant-expression.md) | Constant `Expression(A)` / `Expression(A, BladeMask)`. |
| 4 | [04-docs-changelog.md](./04-docs-changelog.md) | Docs + changelog. |

## Testing as you go

- Algebra tests: `uv run pytest py/tests/algebra/test_galgebra_phase_c.py -q`
- Expression tests: `uv run pytest py/tests/expression/ -q`
- Full suite: `uv run pytest`
- Lint: `uv run ruff check py/pytanga/algebra py/pytanga/expression py/pytanga/codegen`
- Docs: `uv run mkdocs build --strict`
- Binding rebuild smoke: constructing an `Algebra(...)` after touching
  `cpp/`/`_template.cpp`/codegen triggers a JIT rebuild (cache key covers those
  files), so `uv run pytest` itself recompiles the affected binding.

## Non-goals

- No `int`/`list[int]` support for `project_onto` (only `MV | BladeMask`).
- No change to the separate `MV.project(blade)` / `MV.reject(blade)` geometric
  blade projection (that is a different feature).
- No change to the C++ `ProjectTo` template beyond its removal (no attempt to
  keep it as a public utility).
