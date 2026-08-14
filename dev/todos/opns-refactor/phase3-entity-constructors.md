# Phase 3 — MV-Accepting Entity Constructors

**Prerequisites:** Phase 2 (typed analyzers exist and are dispatched from `analysis.py`).

**Goal:** Make `Point(A)`, `Direction(A)`, `Line(A)`, `Plane(A)`, `Circle(A)`,
`Sphere(A)`, `Space(A)`, `PointPair(A)`, `HPoint(A)`, and `HDirection(A)` accept a
single multivector argument and convert it via the typed analyzer — raising if `A`
has the wrong structure. Preserve the E3-vector convenience for `Point`/`Direction`.

Beyond single-arg conversion, **every field of an entity constructor that expects a
`Point`, `Direction`, or scalar also auto-converts a multivector**. For example
`Circle(center_mv, radius_mv, normal_mv)` works with a point-MV, a scalar-MV
(radius), and a direction-MV (normal), each converted via the matching typed
conversion / scalar extractor.

File: `py/pytanga/geometry/entities.py`

---

## 1. Shared MV-detection helper

Add a module-private helper and import the typed analyzers lazily (to avoid a
circular import between `entities.py` and `analysis.py`, which already imports
`entities.py`):

```python
def _is_mv(x):
    return hasattr(x, "_alg")
```

---

## 2. `Point.__init__`

Replace the current `hasattr(x, "_alg")` branch:

```python
def __init__(self, x=0.0, y=0.0, z=0.0):
    if _is_mv(x):
        mv = x
        p = _point_from_mv(mv)   # shared helper below
        object.__setattr__(self, "x", p.x)
        object.__setattr__(self, "y", p.y)
        object.__setattr__(self, "z", p.z)
        return
    object.__setattr__(self, "x", float(x))
    ...
```

`_point_from_mv(mv)`:

1. **E3-vector convenience (Q3).** If `mv` is a plain Euclidean grade-1 vector
   (only `e1/e2/e3` non-zero; no homogeneous `e4/e3`, no `ein/eo/e0`, no `ep/em`),
   return `Point(float(mv[1]), float(mv[2]), float(mv[4]))` when in OPNS; when
   `mv.algebra.opns` is `False`, dualize first before extracting the XYZ parts.
   This keeps `Point(basisE3().e1 + basisE3().e2)` working.
2. Otherwise call the typed analyzer from `geometry.analysis` (`analyze_point(mv)`),
   which raises on mismatch (and on unsupported algebras such as E3).

> The grade-1 plain-vector check is a narrow structural check (all non-zero blades
> have grade 1 and are among ids {1,2,4}), deliberately limited so it never masks a
> genuine mismatch in P3/N3/PGA3 (whose points are not plain E3 vectors).

---

## 3. `Direction.__init__`

Identical pattern, delegating to `_direction_from_mv(mv)`:

1. E3 plain grade-1 vector → extract `(mv[1], mv[2], mv[4])` (dualize if IPNS).
2. Else `analyze_direction(mv)` (raises on mismatch).

---

## 4. Other entity constructors

Add a single-MV constructor that calls the corresponding typed analyzer and copies
fields. Only add MV acceptance where the entity has a meaningful single-MV
representation:

- `Line.__init__` — detect `_is_mv(origin)` and call `analyze_line`; copy
  `origin`, `direction.x/y/z`. Keep `length` resolution (recompute from the
  analyzer's returned `Line`, or leave `None` → visualizer default).
- `Plane.__init__` — `_is_mv(point)` → `analyze_plane`; copy `point`, `normal`,
  and the `span_u`/`span_v`/`extent` left at default.
- `Circle.__init__` — `_is_mv(center)` → `analyze_circle`; copy `center`,
  `radius`, `normal`, `is_imaginary`.
- `Sphere.__init__` — `_is_mv(center)` → `analyze_sphere`; copy `center`,
  `radius`, `is_imaginary`.
- `Space.__init__` — `_is_mv(scale)` → `analyze_space`; copy `scale`.
- `PointPair.__init__` — `_is_mv(point_a)` → `analyze_point_pair`; copy all fields.
- `HPoint.__init__` — `_is_mv(point)` → `analyze_hpoint`; copy `point`, `weight`.
- `HDirection.__init__` — `_is_mv(direction)` → `analyze_hdirection`; copy `direction`.

Each frozen dataclass uses `object.__setattr__`; the numeric/default branch must
not re-enter the MV branch (avoid recursion by branching on `_is_mv` first).

---

## 5. Field-level auto-conversion + scalar-MV extractor

Add a shared helper that converts any argument that is an MV into its **python
value** according to the target field type:

```python
def _coerce(value, target):
    """Convert *value* to *target* type, auto-converting MVs.

    - ``target is Point``:      ``Point(value)`` (typed, + E3 vector shortcut)
    - ``target is Direction``:  ``Direction(value)``
    - ``target is float``:      ``float(_scalar(value))`` where ``_scalar``
      returns ``value.scalar`` for an MV and ``value`` otherwise (must be scalar).
    """
    if target is Point and _is_mv(value):
        return Point(value)
    if target is Direction and _is_mv(value):
        return Direction(value)
    if target is float and _is_mv(value):
        return float(value.scalar)      # scalar MV -> float
    return value
```

Then every entity `__init__` coerces its fields through `_coerce` *before* the
positional/default branch. Using `Circle` as the running example:

```python
def __init__(self, center, radius, normal=None, is_imaginary=False):
    center = _coerce(center, Point)          # A: point MV -> Point
    radius = _coerce(radius, float)          # B: scalar MV -> float
    if normal is not None:
        normal = _coerce(normal, Direction)  # C: direction MV -> Direction
    ...
```

This generalizes the single-arg MV case too: `Circle(center_mv)` only works if the
other required fields are also provided (positional); a **single** MV argument to a
multi-field constructor is handled via the typed whole-entity analyzers of §4 (e.g.
`Circle(circle_mv)`), which is detected when `_is_mv(center)` and the remaining
positional args are absent/default.

Fields to coerce across entities:

| Entity | `Point` fields | `Direction` fields | `float` fields |
|--------|---------------|--------------------|----------------|
| `Point` | — (self) | — | — |
| `Direction` | — (self) | — | — |
| `HPoint` | `point` | — | `weight` |
| `PointPair` | `point_a`, `point_b` | `_direction` | `_separation` |
| `Line` | `origin` | `direction` | `length` |
| `Plane` | `point` | `normal`, `span_u`, `span_v` | `extent` |
| `Circle` | `center` | `normal` | `radius` |
| `Sphere` | `center` | — | `radius` |
| `Space` | — | — | `scale` |
| `HDirection` | — | `direction` | — |

Scalar fields accept a plain `float/int` as before, or a scalar MV (grade-0). A
non-scalar MV passed to a `float` field raises `ValueError` (`_scalar` checks
`value.is_scalar`).

---

## 6. `Line.from_points` auto-converts MV arguments

`Line.from_points(start, end)` currently does `direction = end - start` expecting
two `Point`s. Change it so that when either argument is a multivector it is first
converted via `Point(mv)`:

```python
@classmethod
def from_points(cls, start, end) -> "Line":
    if _is_mv(start):
        start = Point(start)
    if _is_mv(end):
        end = Point(end)
    direction = end - start
    return cls(origin=start, direction=direction, length=direction.mag())
```

`Point(mv)` raises `TypeError` on mismatch, which propagates. Because
`Point.__init__` (rewritten above) already does the right thing for plain E3
vectors and typed analyzers in other algebras, `Line.from_points` needs no
algebra-specific logic.

---

## 7. Tests (Phase 3)

New file `py/tests/geometry/test_entity_constructors.py`:

- `Point(n3_point_mv)` round-trips the coordinates (N3 OPNS and IPNS).
- `Point(p3_point_mv)`, `Point(pga3_point_mv)` round-trip.
- `Point(n3_line_mv)` raises.
- E3 convenience: `Point(e3.vector(1, 2, 3)) == Point(1, 2, 3)`;
  `Direction(e3.vector(1, 0, 0)) == Direction(1, 0, 0)`.
- `Direction(p3_direction_mv)` round-trips.
- `Line(n3_line_mv)`, `Plane(n3_plane_mv)`, `Circle(n3_circle_mv)`,
  `Sphere(n3_sphere_mv)`, `Space(n3_space_mv)`, `PointPair(...)`, `HPoint(...)`,
  `HDirection(...)` round-trip.
- `Line(n3_point_mv)` raises.
- `Space(n3_point_mv)` raises.
- Field auto-conversion: `Circle(point_mv, radius_mv, normal_mv)` with a point-MV,
  scalar-MV, and direction-MV round-trips; a non-scalar MV in `radius` raises.
- `Line.from_points(n3_point_mv_a, n3_point_mv_b)` round-trips to the expected
  `origin`/`direction`.
- `Line.from_points(point_mv, point_mv)` in E3 (plain vectors) preserves the
  convenience.
- `Line.from_points(n3_line_mv, point_mv)` raises (first arg is a line MV).
- Unsupported algebra: `Point(e3.vector(...))` still succeeds via convenience,
  but `analyze_point(e3.vector(...))` raises (covered in Phase 2 tests).

No existing tests change in Phase 3.

---

## 8. Implementation Checklist

- [ ] Add `_is_mv` and `_point_from_mv` / `_direction_from_mv` helpers
- [ ] Rewrite `Point.__init__` and `Direction.__init__`
- [ ] Add MV acceptance to `Line`, `Plane`, `Circle`, `Sphere`, `Space`,
      `PointPair`, `HPoint`, `HDirection`
- [ ] Add `_coerce`/`_scalar` helpers and coerce every `Point`/`Direction`/`float` field
- [ ] Auto-convert MV args in `Line.from_points`
- [ ] Add `py/tests/geometry/test_entity_constructors.py`
- [ ] Run: `pytest py/tests/geometry/test_entity_constructors.py -q`

---

## 9. Verification

- [ ] Every supported entity constructor converts a matching MV to the expected entity
- [ ] Mismatched MVs raise `TypeError` from the underlying typed analyzer
- [ ] E3 grade-1 vector convenience still works for `Point`/`Direction`
- [ ] `Circle(point_mv, radius_mv, normal_mv)` auto-converts all fields
- [ ] `Line.from_points(mv, mv)` converts multivectors automatically