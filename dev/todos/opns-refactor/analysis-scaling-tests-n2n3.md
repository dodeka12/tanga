# Analysis Correctness Tests — N2 / N3

**Context.** The N2 circle analysis had a homogeneous-scale bug: the IPNS
circle `C*` was not normalized by its `e₀` coefficient before extracting
centre/radius, so a globally scaled MV produced a wrong radius. This was
fixed in `analysis_n2.py::_decompose_circle` (normalize `C* = C* / f_eo`
first) and mirrored into the other N2/N3 analyzers.

This plan adds regression tests that build entities **directly from point
blades** (outer products of conformal points) and verify the analysis
recovers the correct numeric parameters, plus scale-by-2 round-trip tests
for every N2/N3 entity. No production code is expected to change unless a
test exposes a remaining normalization bug — in that case the fix goes in
`py/pytanga/geometry/analysis_n2.py` / `analysis_n3.py`.

All test code goes in the existing files:

- `py/tests/geometry/test_geometry_n2_analysis.py`
- `py/tests/geometry/test_geometry_n3_analysis.py`

---

## Helper patterns (used by every step)

For both files, the existing `b` fixture (`BasisN2()` / `BasisN3()`) is the
algebra. Points are built with `create_entity(b, Point(x, y, z))` (returns
the OPNS conformal point `Cop(p)`). Blades for sub-entities are formed with
`.op(…)`.

```python
def _pts(b, *coords):
    return [create_entity(b, Point(*c)) for c in coords]
```

---

## Step 1 — N2: circle from three points (radius 1)

In `test_geometry_n2_analysis.py`, add a test that:

1. Picks centre `C = Point(2, 3, 0)` and three points at Euclidean
   distance 1 from C, e.g. `(3,3,0)`, `(2,4,0)`, `(1,3,0)`.
2. Builds the circle blade as `p1.op(p2).op(p3)`.
3. `r = analyze_entity(blade)`.
4. Asserts:
   - `isinstance(r, Circle)`
   - `r.center ≈ (2, 3, 0)`
   - `r.radius ≈ 1.0`
   - `r.normal ≈ (0, 0, 1)` (always +z in 2D)
   - `not r.is_imaginary`

---

## Step 2 — N3: circle from three points (radius 1, plane normal)

In `test_geometry_n3_analysis.py`, add a test that:

1. Picks centre `C = Point(1, 2, 3)` and three coplanar points at radius 1
   in the plane `z = 3`, e.g. `(2,2,3)`, `(1,3,3)`, `(0,2,3)`.
2. Builds the circle blade as `p1.op(p2).op(p3)` (grade 3).
3. `r = analyze_entity(blade)` routes to `_decompose_circle`.
4. Asserts:
   - `isinstance(r, Circle)`
   - `r.center ≈ (1, 2, 3)`
   - `r.radius ≈ 1.0`
   - `r.normal` is `(0, 0, 1)` or `(0, 0, -1)` (allow global sign)
   - `not r.is_imaginary`

---

## Step 3 — N3: sphere from four points (radius 1)

In `test_geometry_n3_analysis.py`, add a test that:

1. Picks centre `C = Point(1, 2, 3)` and four non-coplanar points at radius
   1, e.g. `(2,2,3)`, `(1,3,3)`, `(1,2,4)`, `(0,2,3)`.
2. Builds the sphere blade as `p1.op(p2).op(p3).op(p4)` (grade 4).
3. `r = analyze_entity(blade)` routes to `_sphere_or_plane_n3_opns`.
4. Asserts:
   - `isinstance(r, Sphere)`
   - `r.center ≈ (1, 2, 3)`
   - `r.radius ≈ 1.0`
   - `not r.is_imaginary`

---

## Step 4 — N2: point pair from two points

In `test_geometry_n2_analysis.py`, add a test that:

1. Picks `A = Point(1, 0, 0)`, `B = Point(3, 0, 0)`.
2. Builds `pp = pa.op(pb)` (grade 2).
3. `r = analyze_entity(pp)`.
4. Asserts:
   - `isinstance(r, PointPair)`
   - midpoint ≈ `(2, 0, 0)` (average of `r.point_a`/`r.point_b`)
   - separation ≈ `2.0` (Euclidean distance between the two points)
   - `not r.is_imaginary`

---

## Step 5 — N3: point pair from two points

Same as Step 4 but in `test_geometry_n3_analysis.py`, using 3D points
`A = Point(1, 0, 0)`, `B = Point(3, 0, 0)` (or a 3D offset pair such as
`(1,2,3)`–`(4,2,3)`). Assert midpoint and separation 3, direction along x.

---

## Step 6 — N2: scale-by-2 round-trip for every entity

In `test_geometry_n2_analysis.py`, for each entity below: create it with
`create_entity(b, <entity>)`, scale the MV by 2 (`mv2 = mv * 2.0`), analyze,
and assert the geometric parameters are unchanged (a global scale must not
change the recovered geometry). Entities to cover:

| Entity | Invariant assertions |
|--------|----------------------|
| `Point(3, -2, 0)` | x/y/z unchanged |
| `Direction(1, 2, 0)` | unit direction unchanged |
| `PointPair(Point(1,0,0), Point(3,0,0))` | midpoint + separation 2 unchanged |
| `HPoint(Point(2,-1,0), weight=2.5)` | point unchanged; **weight = 2 × 2.5** (weight is a homogeneous factor and scales with the MV) |
| `HDirection(Direction(1,2,0))` | unit direction unchanged |
| `Line(Point(1,2,0), Direction(1,2,0))` | direction and on-line origin unchanged |
| `Circle(Point(1,0,0), radius=2.5, normal=+z)` | centre + radius 2.5 unchanged |
| `Sphere(Point(2,-1,0), radius=2.5)` → `Circle` | centre + radius 2.5 unchanged |
| `Space(scale=2.5)` | **scale = 5.0** (Space.scale is the MV magnitude, so it doubles) |

> Note the two flagged cases: `HPoint.weight` and `Space.scale` are the only
> parameters that are expected to scale by 2. Everything else must be
> scale-invariant.

---

## Step 7 — N3: scale-by-2 round-trip for every entity

Same pattern in `test_geometry_n3_analysis.py`:

| Entity | Invariant assertions |
|--------|----------------------|
| `Point(3,-2,1)` | x/y/z unchanged |
| `Direction(1,2,3)` | unit direction unchanged |
| `PointPair(Point(1,0,0), Point(3,0,0))` | midpoint + separation 2 unchanged |
| `HPoint(Point(2,-1,1), weight=2.5)` | point unchanged; weight = 5.0 |
| `HDirection(Direction(1,2,3))` | unit direction unchanged |
| `Line(Point(1,2,3), Direction(1,2,3))` | direction + on-line origin unchanged |
| `Circle(Point(1,2,3), radius=2.5, normal=(0,0,1))` | centre + radius + normal unchanged |
| `Plane(Point(0,0,4), Direction(0,0,1))` | point + unit normal unchanged |
| `Sphere(Point(2,-1,1), radius=2.5)` | centre + radius unchanged |
| `Space(scale=2.5)` | scale = 5.0 |

---

## Step 8 — Verification

- `uv run python -m pytest py/tests/geometry/test_geometry_n2_analysis.py py/tests/geometry/test_geometry_n3_analysis.py -q`
- If a scale-invariant assertion fails, fix the corresponding normalisation
  in `py/pytanga/geometry/analysis_n2.py` / `analysis_n3.py` (do **not**
  relax the test).
- Run the full geometry suite: `uv run python -m pytest py/tests/geometry -q`

---

## Verification checklist

- [x] N2 circle-from-3-points returns correct centre/radius/normal
- [x] N3 circle-from-3-points returns correct centre/radius/normal
- [x] N3 sphere-from-4-points returns correct centre/radius
- [ ] N2 + N3 point-pair-from-2-points returns correct midpoint/separation
- [ ] N2 + N3 scale-by-2 tests: all geometric params invariant; HPoint.weight and Space.scale double
- [ ] Full geometry test suite passes