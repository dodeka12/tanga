# Typing & annotations

How the Python side of TanGA is typed, and how that typing is enforced.

`py/pytanga` and `py/examples` are **fully annotated** — every public and
private function, method, dataclass field, and module-level constant declares
its types.  Two independent gates keep it that way:

| Gate | Command | Catches |
| --- | --- | --- |
| `ty` | `uv run ty check` | wrong types: bad calls, bad attributes, unsound returns, unresolved names |
| ruff `ANN` | `uv run ruff check .` | *missing* annotations (coverage) |

Both run as a pre-commit hook (`ty`) and in the CI `lint` job (see
`.pre-commit-config.yaml`, `.github/workflows/ci.yml`).  `ty` checks the trees
listed in `[tool.ty.src] include` (`py/pytanga`, `py/examples`); ruff covers the
whole repository, with `py/tests/**` deferred from the coverage rule (see
[Deferred scope](#deferred-scope)).

This note is the *policy*; the phase-by-phase record of how the (initially 584
diagnostics / 935 missing annotations) were resolved lives in
`dev/todos/ty-type-hints/`.

## Rule 1 — annotate everything, always

New code — library, example, script, notebook cell, or tool — ships with
annotations for every parameter and return value, including `-> None` and
including private helpers (`_foo`).  Do not add an unannotated function "just
for now": `ruff ANN` rejects it, and the annotation is cheapest to write while
the types are still in your head.

```python
# ✅
def _axis_ticks(
    self, scale: Scale, lo: float, hi: float
) -> list[tuple[float, str]]: ...

# ❌ (ANN001/ANN202)
def _axis_ticks(self, scale, lo, hi): ...
```

## Rule 2 — avoid `Any`; make it a deliberate, documented choice

`ANN401` is intentionally **not** enabled, because a handful of surfaces are
dynamic by nature (the C++ binding dispatch layer, `**properties: Any` payload
dicts, handler `value` arguments, the loosely-typed example helpers).  That
relaxation is not a licence to reach for `Any`: it means the gate cannot catch
it, so *review* has to.

Before writing `Any`, exhaust the alternatives:

1. **A real type, union, or `Sequence`.**  Most `Any`s hide a type you already
   know (`Path | None`, `str | None`, `Mapping[str, object]`).
2. **`object`** when the value genuinely can be anything you only introspect
   (`isinstance`-dispatch helpers) — but see Rule 4 on dispatchers.
3. **A `Protocol`** when you need structure, not identity — see
   `viz/_basis_views.py` (`ConformalBasis`, `PGABasis2D|3D`), `CreateModule`,
   and `StylesMap` for the pattern: declare the duck-typed contract, then
   `cast` once at the binding boundary where the runtime contract is guaranteed.
4. **A `TypeVar`** (or `@overload`) for "same type in, same type out".

When `Any` is genuinely right, keep it *at the edge* — an untyped C++ return
becomes a `float`, a `tuple[float, float, float]`, or a documented alias as
soon as it crosses into library code.

## Rule 3 — never leave a declared type a lie

An annotation that disagrees with the runtime is worse than no annotation,
because both the reader and the checker trust it.  Two directions:

- **The runtime accepts more than the annotation** → widen it.  Examples from
  this codebase: `Sequence[...]` instead of `list[...]` (list invariance makes
  `list[MV]` *not* assignable to `list[MV | float]`), `EAnchor | str` /
  `EStackDirection | str` / `EProduct | str` for `StrEnum` parameters whose
  string values the docs and tests already pass, and `VizInputType` for the
  `update_entity()`-style entry points that resolve MVs internally.
- **The runtime accepts less than the annotation** (i.e. it would only fail
  later) → reject it early with a clear `ValueError`/`TypeError`, as
  `scale_matrix()` does for a half-specified `sy`/`sz` pair.

## Rule 4 — prefer proving over casting

`cast` is a promise to the checker; the goal is to need as few as possible.

- **`TypeIs`** turns a hand-written predicate into a narrowing test:
  `_is_number_value(value: Any) -> TypeIs[int | float]`, `entity._util._is_mv`.
  Use it instead of `hasattr` duck-checks in `if` conditions — `hasattr`
  produces synthesized protocol intersections that no downstream call accepts.
- **`isinstance` + `assert`** in examples and scripts documents the runtime
  invariant *and* narrows the type.
- **`field(default_factory=...)`** removes the "optional then always set"
  field, which in turn removes the `X | None` union and every `.` access that
  guarded it.
- **Hoist to the common base** when sibling classes duplicate a method with the
  same signature (`VizNode.patch`, `VizNode.style`) — the base declaration is
  what lets call sites stop narrowing.
- **`@overload`** is the tool for dispatchers whose return type depends on the
  argument (`Geometry.__call__`, `Visualizer.add`, `MVTensor.__getitem__`).
  Returning `object` from a dispatcher is not "safe", it is unusable: every
  call site then needs a cast.

## Rule 5 — no `None`-then-assign attributes

Lifecycle hooks (`init()`, `build()`, `mount()`) that assign an attribute after
`__init__` should declare it **non-optional on the class** rather than
initialising it to `None`:

```python
class TableEditingApp(VisualizerApp):
    """..."""

    #: Created in :meth:`init`, which the app framework calls before any event.
    _table: TableView
```

Every event handler can then use `self._table.undo()` directly instead of
carrying a `None` check.

## Rule 6 — narrow with a helper when the checker loses the fact

`assert isinstance(...)` narrows in the current scope, **not** inside a
comprehension or a nested function — and ty widens narrowings again inside
loops.  In an animation loop a module-level `assert` does not protect a call
made in the loop body.  The fix is a tiny helper whose return type *is* the
narrowed type:

```python
def _single_mv(value: "MV | list[MV]") -> MV:
    """Narrow an `MV | list[MV]` result to the single MV it holds here."""
    assert isinstance(value, MV), "expected a single multivector"
    return value
```

`py/examples/ga/numerics/solver_rotor_estimation.py` and
`py/examples/viz/animation/two_body_gravity.py` (`_as_direction`) use this.

## Rule 7 — suppressions are documented false positives

When a diagnostic is wrong (not the code), suppress it narrowly and say why:

```python
return f(a_ids, b_ids, left, complete)  # ty: ignore[unsound-return-statement]  # binding resolved by name via getattr
```

Always the narrowest rule id, always a trailing reason, never a blanket
`# type: ignore`.  The suppressions currently in the tree are:

| Site | Rule | Why it is a false positive |
| --- | --- | --- |
| `py/pytanga/blade_mask/_dispatch.py` | `unsound-return-statement` | the binding is resolved by name via `getattr` |
| `py/examples/ga/basis/basis_usage.py` (3 lines) | `unresolved-reference` | the blade names are injected by `globals().update()`; the example documents this |

## Deferred scope

- **`py/tests/**`** — the test suite is not annotated yet and is excluded from
  the ANN rule (`[tool.ruff.lint.per-file-ignores]`, which also carries the
  suite's pre-existing star-import lint debt).  New tests should still be
  annotated where practical.
- **Notebooks** — the `docs/py/viz/**/*.ipynb` documentation notebooks *are*
  annotated (they are part of `ruff check .`), but `ty` does not read them.

## Tooling reference

```bash
uv run ty check                     # correctness (py/pytanga + py/examples)
uv run ruff check .                 # lint, incl. ANN coverage
uv run ruff format .                # formatting
uv run pre-commit run --all-files   # all gates
```

`ty`'s rule severities live in `[tool.ty.rules]` in `pyproject.toml`
(`unsound-return-statement`, `missing-type-argument` and
`dynamic-function-decorator-return` are errors;
`possibly-unresolved-reference` warns).
