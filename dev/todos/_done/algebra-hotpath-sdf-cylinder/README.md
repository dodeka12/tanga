# Algebra hot-path + SDF cylinder fixes — Overview

**Created:** 2026-09-24 | **Status:** Done | **Branch:** `fix/algebra-hotpath-sdf-cylinder`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Fix three reported issues, all internal pytanga changes with no public-API
break:

1. **String-keyed blade-name parsing is un-cached**
   (`_input/pytanga-mv-string-blade-key-parsing-overhead.md`) — `MV.__getitem__`
   / `__setitem__` re-parse the same blade name (e.g. `"e14"`) on every call.
   Cache the parse.
2. **`Algebra` operators re-check a per-instance-constant `modulus` on every
   call** (`_input/pytanga-mv-operator-dispatch-overhead.md`) — resolve the
   modulus branch once per `Algebra` instance.
3. **`SdfObject(Cylinder(...))` mis-applies `align_center`**
   (`_input/pytanga-sdf-cylinder-align-center-offset-bug.md`) — the SDF cylinder
   offset uses `length/2` where it should use `length`.

Issue 3 makes the SDF renderer match the already-documented `align_center`
semantics; issues 1–2 are pure hot-path optimizations with no behavior change.

## Architecture (short)

- **Blade-name parsing** lives in
  `py/pytanga/algebra/_blade_names.py::blade_id_signed` (a pure function of
  `(name, dim, comma)`), reached from `Algebra._resolve_key_signed`
  (`py/pytanga/algebra/_algebra.py`). Caching the string branch once, per
  algebra, speeds every string-keyed access (`mv["e14"]`, `mv["e12"] = x`,
  string keys in `Algebra.multivector`) with zero caller changes.
- **Operator dispatch** lives in `py/pytanga/algebra/_algebra.py`
  (`add`/`sub`/`scale`/`gp`/`op`/`ip`); each re-checks
  `self._modulus is not None` on every call even though `_modulus` is assigned
  exactly once in `__init__` and never reassigned. Branch-free implementations
  are bound once to private `_*_impl` attributes, and the `MV` dunders call them
  directly; the public methods remain for direct callers.
- **SDF cylinder** lives in `py/pytanga/viz/sdf/object.py::_cylinder_node`. The
  mesh renderer (`py/pytanga/viz/_decompose.py::_entity_decompose`) already
  computes the correct `offset = length * (0.5 - align_center)`.

### Fixed contract (do not change across phases)

- `Algebra._resolve_key_signed(key) -> tuple[int, int]` — signature and return
  value unchanged; a per-algebra `dict[str, tuple[int, int]]` caches only the
  string branch. `blade_id_signed` stays a pure, uncached function.
- `Algebra.add/sub/scale/gp/op/ip` — public signatures and results unchanged.
  Branch-free `_*_impl` implementations are bound once at construction, and the
  `MV` dunders route through them; the public methods stay as the documented
  entry points.
- `_cylinder_node` offset — `offset = float(entity.length) * (0.5 -
  float(entity.align_center))` (matches `_decompose.py`). `half` is still
  passed to `capped_cylinder(half, ...)` as the half-height.

## Decisions (confirmed)

- **Cache site = per-algebra, in `Algebra._resolve_key_signed`** (report fix #1,
  the per-algebra-dict alternative). A `dict[str, tuple[int, int]]` on each
  `Algebra`, populated lazily on the string branch: the cache is scoped to (and
  freed with) the algebra, the key is just the blade name (dim/comma are
  per-algebra constants), and there is no global mutable state.
- **Operator fix = bind branch-free implementations to private `_*_impl`
  attributes in `__init__`**, and route the `MV` dunders through them. (The
  report's rebind-the-public-methods variant breaks the repo's `ty` gate, so we
  keep the public methods and change the `MV` call sites instead.)
- **No API/DSL change.** The report's "Not pursued" auto-compile of imperative
  `MV` functions via `Variable`/`Expression` is out of scope; downstream callers
  use the existing `Expression.compile()` path.
- **SDF fix changes only the `offset` line** and updates the one existing test
  that currently asserts the buggy value.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-blade-name-cache.md](./01-blade-name-cache.md) | Cache `_resolve_key_signed` string branch per algebra |
| 2 | [02-operator-dispatch.md](./02-operator-dispatch.md) | Hoist the per-call `modulus` branch out of `Algebra` operators |
| 3 | [03-sdf-cylinder-offset.md](./03-sdf-cylinder-offset.md) | Fix `_cylinder_node` `align_center` offset + update test |
| 4 | [04-docs-changelog.md](./04-docs-changelog.md) | Branch changelog |

## Testing as you go

```bash
uv run pytest py/tests/algebra/test_resolve_key_cache.py -q      # phase 1
uv run pytest py/tests/algebra py/tests/test_modular.py -q       # phase 2
uv run pytest py/tests/viz/sdf/test_sdf_object.py -q             # phase 3
uv run ruff check py/pytanga/algebra py/pytanga/viz/sdf          # lint (each phase)
uv run ty check                                                  # type gate (phase 2)
uv run pytest -q                                                 # full suite (before PR)
```

## Non-goals

- No auto-trace/compile of imperative `MV` functions (report #2 "Not pursued").
- No change to `to_matrix`/`from_matrix` or `BladeMask` — those are already the
  documented bulk fast path; the report's "fix #2" convenience `MV.coeffs` /
  `Algebra.from_coeffs` wrappers are not included.
- No change to the `MV.__add__`/`__mul__` `isinstance` dispatch structure — the
  `MV` dunders keep their `isinstance` checks; only the operator method they
  call changes (from `Algebra.add/gp/...` to the bound `_*_impl`).
- No downstream `wafer_grinding`/application changes.
