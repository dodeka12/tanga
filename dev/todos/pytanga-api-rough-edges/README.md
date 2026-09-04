# pytanga API rough edges — Overview

**Created:** 2026-09-04 | **Status:** Done | **Branch:** `feat/view-architecture`

## Goal

Close four small, independent `pytanga` API rough edges that surfaced while
building the (external) `wafer_grinding` inertia/`MassObject` code, as captured
in `dev/notes/pytanga-expression-call-return-type-and-wedge-operand-order.md`
and `dev/notes/pytanga-sdf-group-composition-and-docs.md`:

1. `Expression.__call__`'s `MV | Expression | list` return type can't be
   narrowed by the caller → add intent-specific `bind()` / `evaluate()`.
2. A constant `MV` on the left of `^` / `|` with a `Variable`/`Expression` on
   the right raises (`AttributeError`) instead of building an `Expression` →
   make `MV.__xor__` / `MV.__or__` return `NotImplemented` for non-`MV`
   operands (the reflected dunders already exist).
3. `pytanga.viz._nodes.Transform` can't be built from a GA operator and isn't
   exported → add `Transform.from_operator()` and export `Transform`.
4. The standard viewer's SDF CSG model (`Composed`/`SdfGroup`/`Combine`) has no
   smooth-blending (`smooth_union`/`smooth_intersection`/`smooth_subtract` +
   `smoothness`), even though the GLSL smooth combinators already exist and the
   standalone `SdfVisualizer` path already uses them.

> Note: the "unified SDF object model" (`SdfStyle`, `SdfObject`, `Combine`,
> `Composed`, `SdfGroup` accepted by `Visualizer.add()`/`.new()`) described in
> note 2 item 1 is **already implemented and documented** in this branch — that
> item is a release-management ask, not a code change, and is out of scope here.

## Architecture (short)

Four independent, minimally-coupled changes across three subsystems:

- **Expression** (`py/pytanga/expression/_expression.py`,
  `py/pytanga/algebra/_mv.py`) — `bind`/`evaluate` delegate to the existing
  `_evaluate()` and narrow with a runtime check; the `MV` operator guard is a
  two-line change mirroring `MV.__mul__`.
- **Viz nodes** (`py/pytanga/viz/_nodes.py`, `py/pytanga/viz/__init__.py`) —
  `Transform.from_operator()` reuses the existing
  `_transforms.operator_to_matrix()` that `VizSceneObject.apply_transform()`
  already relies on.
- **SDF smooth CSG** (`py/pytanga/viz/sdf/*` + `templates/renderers/sdf/glsl.js`
  + `templates/sdf/objects/combinators.js`) — thread a `smoothness` value from
  Python `SdfElement`/`Combine`/`Composed`/`SdfGroup` onto the serialized
  `SdfNode` tree, and emit the already-defined GLSL `opSmooth*` folds.

### Fixed contract

```python
# Expression (and AffineExpression) — __call__ unchanged as the dynamic fallback.
Expression.bind(**kwargs) -> Expression      # raise ValueError if fully collapsed (MV/list)
Expression.evaluate(**kwargs) -> MV          # raise ValueError unless a plain MV results
AffineExpression.bind(**kwargs) -> AffineExpression
AffineExpression.evaluate(**kwargs) -> MV

# MV reflected operators
mv ^ variable / mv ^ expr / mv | variable / mv | expr  -> Expression   # was AttributeError
mv * variable / mv * expr                              -> Expression   # already works

# Transform
Transform.from_operator(op: Translator | Rotor | GeneralRotor | Motor | Dilator) -> Transform
from pytanga.viz import Transform   # now public (added to __all__)
```

```python
# SDF smooth CSG — Python model + wire contract
class ECompose(StrEnum):
    SMOOTH_UNION = "smooth_union"
    SMOOTH_INTERSECTION = "smooth_intersection"
    SMOOTH_SUBTRACT = "smooth_subtract"   # valid fold modes (XOR stays binary-only)

SdfNode.smoothness: float | None = None    # emitted in to_dict() as "smoothness"
SdfStyle.smoothness: float | None = None   # emitted in to_dict()

Composed(sphere(1.0), (capped_cylinder(1.0, 0.4), "smooth_union", 0.15))  # 3-tuple form
Combine(ECompose.SMOOTH_UNION, a, b, smoothness=0.15)
```

The frontend default `smoothness` is `0.1` (matches the existing
`composer.js` `SMOOTHNESS_DEFAULT`); `None` means "use the frontend default".

## Decisions (confirmed)

- **`bind`/`evaluate` raise, not cast.** A runtime `ValueError` is raised when
  the result's concrete type doesn't match the caller's stated intent (the same
  philosophy as the `_as_expression` `assert isinstance(...)` workaround). This
  fails loudly at the point of a wrong assumption rather than silently
  mis-typing.
- **`AffineExpression` gets the same `bind`/`evaluate`.** It has the identical
  `MV | AffineExpression | list` return-type problem; leaving it out would make
  the API asymmetric for no reason.
- **Smooth CSG includes the full Python + frontend path** (phases 04 and 05),
  but phase 05 is the riskiest and can be deferred/descoped without blocking
  phases 01–04 (which are independent).
- **`smoothness` lives per-member on the `SdfNode` tree** (not just on
  `SdfStyle`), because the `Composed`/`SdfGroup` fold is what needs a
  per-join blend; `SdfStyle.smoothness` is added as a convenience default that
  per-member values can override.
- **`parts` stays a 2-tuple** `(element, mode)`; `smoothness` is stamped onto
  the member element (an `SdfElement`/`SdfNode` field) rather than widening the
  tuple to 3, to avoid touching the serializer's unpacking sites.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-mv-reflected-wedge-and-dot.md](./01-mv-reflected-wedge-and-dot.md) | `MV.__xor__`/`__or__` return `NotImplemented` for non-`MV` operands. |
| 2 | [02-expression-bind-evaluate.md](./02-expression-bind-evaluate.md) | `Expression.bind`/`evaluate` (+ `AffineExpression`). |
| 3 | [03-transform-from-operator.md](./03-transform-from-operator.md) | `Transform.from_operator()` + public export. |
| 4 | [04-sdf-smooth-csg-python.md](./04-sdf-smooth-csg-python.md) | Smooth modes + `smoothness` through the Python SDF model and serializer. |
| 5 | [05-sdf-smooth-csg-frontend.md](./05-sdf-smooth-csg-frontend.md) | Emit smooth folds in the proxy shader and `Combine`/`group` tree emitter. |
| 6 | [06-docs-changelog.md](./06-docs-changelog.md) | Docs + branch changelog. |

## Testing as you go

- Python (expression/algebra): `uv run pytest py/tests/expression/ py/tests/algebra/ -q`
- Python (viz nodes): `uv run pytest py/tests/viz/test_nodes.py -q`
- Python (SDF): `uv run pytest py/tests/viz/sdf/ -q`
- JS syntax: `node --input-type=module --check <file>` / `node --check <file>`
- JS smoke: `node dev/src/sdf_composer_smoke.mjs`
- Lint: `uv run ruff check py/`
- Full gate: `uv run pytest -q`

## Non-goals

- Publishing a new `tanga-py` release (note 2 item 1) — release management,
  not a code change.
- `SdfGroup`/`SdfObject`/`Composed` accepted by `Visualizer.add()`/`.new()` —
  already implemented.
- `VizGroup.add_child()` accepting a *raw* `SdfElement`/geometry entity — the
  working pattern today is `viz.new(...)`/`VizObjectRef.add(...)`/`.parent`,
  which already re-parents SDF children under a `VizGroup`; a coercing
  `add_child` would need detached-`VizGroup` id-assignment semantics that are
  out of scope here.
- Smooth CSG on the standalone `SdfVisualizer` path — already implemented.
- `Expression`-related `ty`/pyright narrowing beyond the `bind`/`evaluate`
  runtime-narrowing methods (no generic/`Literal` overloads on `__call__`).
