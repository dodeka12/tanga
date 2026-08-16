# Random entity generators for the geometry submodule — DONE

## Summary

Random geometric entity generation was moved out of the basis classes and into the
geometry submodule as lazy **generator objects** consumed by `Geometry.__call__`.
The generators produce `Point`/`Direction` dataclasses, which `Geometry` then routes
through the algebra's existing `create` dispatcher — so multivectors automatically
honor the algebra's OPNS/IPNS flag.

The earlier module-level `random_*` functions and the `Geometry.random_*` forwarder
methods were removed in favor of this generator API (they existed only in uncommitted
working state and were fully superseded).

## Implemented design

### `py/pytanga/geometry/random.py` (new)

Distribution hierarchy (scalar samplers, each `__call__(rng) -> float`):
- `Distribution` — abstract base.
- `Uniform(low, high)` — `rng.uniform`.
- `Normal(mean=0.0, stddev=1.0)` — `rng.normal`.

Entity generator hierarchy (each `__call__(rng) -> Entity | list[Entity]`):
- `RndEntity` — common base for future random-entity generators.
- `RndPoint(x=(-1,1), y=(-1,1), z=(-1,1), *, count=None)`
- `RndDirection(x=(-1,1), y=(-1,1), z=(-1,1), *, count=None)`

Coordinate specs accept a `Distribution` instance or a 2-tuple `(low, high)`
(interpreted as `Uniform`). `count=None` → single entity; `count=n` → list of n.
Helper `_as_distribution(spec)` normalizes tuple specs.

### `py/pytanga/geometry/_geometry.py`

- `Geometry(algebra, *, seed=None)` stores a seeded `numpy.random.Generator`
  (`__slots__ = ("_algebra", "_rng")`).
- Added `rng` read-only property.
- `Geometry.__call__` dispatch order:
  1. `RndEntity` → call with `self._rng`, then `create()` the resulting entity/list.
  2. `list`/`tuple` → recurse over each element.
  3. `Entity`/`Operator` → `create()`.
  4. `MV` → `analyze()`.
- Removed the eight `Geometry.random_*` forwarders.

### `py/pytanga/geometry/__init__.py`

Exports the new classes (`Distribution`, `Uniform`, `Normal`, `RndEntity`,
`RndPoint`, `RndDirection`) and dropped the old `random_*` function exports.

### Examples

`py/examples/numerics/solver_point_line_p3.py` and
`py/examples/tensor/rotor-point-on-ray_01.py` now seed a `Geometry` and use the
generator API instead of `P3.rng.uniform(...)`:

```python
geo = Geometry(P3, seed=0)
def _rnd_point() -> MV:
    return geo(RndPoint((-2, 2), (-2, 2), (-2, 2)))
def _rnd_direction() -> MV:
    return geo(RndDirection((-0.1, 0.1), (-0.1, 0.1), (-0.1, 0.1)))
```

### Tests

`py/tests/geometry/test_geometry_random.py` (rewritten) covers:
- direct generator calls return `Point`/`Direction`; `count` returns lists,
- `Normal`/`Uniform` sampling behavior and bounds,
- unknown spec raises `TypeError`,
- `Geometry.__call__` integration (single `RndPoint`, `count=`, list comprehension,
  `Normal` distribution) across all 8 algebras,
- determinism via `Geometry(..., seed=...)`,
- `geo.rng` is a `numpy.random.Generator`.

### Docs

- `docs/py/geometry/random.md` (new) documents seeding, `RndPoint`/`RndDirection`,
  `count`, `Uniform`/`Normal`, and the `Geometry.__call__` dispatch.
- `docs/py/geometry/index.md` link text updated.
- `mkdocs.yml` nav entry added (`Random generation: py/geometry/random.md`).

## Usage

```python
geo = Geometry(BasisP3(), seed=0)
p  = geo(RndPoint((-1, 1), (-2, 3), (1, 2)))              # single point MV
pts = geo(RndPoint((-1, 1), (-2, 3), (1, 2), count=10))   # list of 10 MVs
pts = geo([RndPoint((-1, 1), (-2, 3), (1, 2)) for _ in range(10)])
mv = geo(RndPoint(Normal(0, 1), (-1, 1), Normal(2, 0.1)))
```

## Verification performed

- `python3 -m py_compile` on all changed files: OK.
- `uv run pytest py/tests/geometry/test_geometry_random.py`: 56 passed.
- `uv run pytest py/tests/geometry/test_geometry_convenience.py`: 13 passed
  (no regression in `Geometry.__call__`).
- Grep confirmed no leftover `random_*` module functions or `.random_point` references.