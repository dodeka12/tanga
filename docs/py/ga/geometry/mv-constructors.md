# Constructing Entities and Operators from Multivectors

Every entity and operator dataclass in `pytanga.geometry` can be initialized
from a plain multivector (`MV`) **in addition** to its regular scalar/field
arguments.  The multivector is converted by running it through the matching
typed analyzer (for example, `Circle(mv)` calls
`analyze_circle(mv)`), so you can round-trip any MV that represents a circle
back into an entity.

The same auto-conversion applies to the nested fields used by the various
factory helpers — `Line.from_points`, `Plane.from_corner_and_span`, and
friends accept `MV` arguments wherever they accept a `Point`/`Direction`.

## Why this matters

Multivectors carry their algebra (and therefore their OPNS/IPNS
interpretation) with them.  Passing an `MV` into an entity constructor lets
you normalize a computed result into a typed entity without writing explicit
`analyze_*()` calls:

```python
from pytanga.basis import BasisN3
from pytanga.geometry import Geometry, Point

n3 = BasisN3()
geo = Geometry(n3)
mv = geo.create(Point(1, 2, 3))
# ... later, recover the geometric meaning:
recovered = Point(mv)
print(recovered)       # Point(1.00, 2.00, 3.00)
```

## Entities accepting an MV

| Constructor | Analyzer used | Notes |
|-------------|---------------|-------|
| `Point(mv)` | `analyze_point` | Reads `e1`/`e2`/`e3` components |
| `Direction(mv)` | `analyze_direction` | Reads `e1`/`e2`/`e3` components |
| `Line(mv)` | `analyze_line` | Sets `origin`, `direction`, `length` |
| `Plane(mv)` | `analyze_plane` | Sets `point`, `normal` (+ optional spans/extent) |
| `Circle(mv)` | `analyze_circle` | Sets `center`, `radius`, `normal`, `is_imaginary` |
| `Sphere(mv)` | `analyze_sphere` | Sets `center`, `radius`, `is_imaginary` |
| `PointPair(mv)` | `analyze_point_pair` | Sets `point_a`, `point_b`, `is_imaginary` |
| `HPoint(mv)` | `analyze_hpoint` | Sets `point`, `weight` |
| `HDirection(mv)` | `analyze_hdirection` | Sets `direction` |
| `Space(mv)` | `analyze_space` | Accepts a scalar MV (grade 0) directly |

The imaginary variants (`ImagCircle`, `ImagSphere`, `ImagPointPair`) are
subclasses of these and accept an MV the same way.

## Operators accepting an MV

The operator dataclasses are algebra-independent, but construction from an MV is
currently **not** automatic (operators require `analyze_operator(mv)` rather
than a constructor).  Use the analysis pipeline directly:

```python
from pytanga.geometry import Rotor, analyze_operator

rotor = analyze_operator(rotor_mv)   # → Rotor(...)
```

## Factory methods with auto-conversion

### `Line.from_points(start, end)`

Builds a line segment; both arguments are coerced via `Point(·)`, so MVs that
represent points work directly:

```python
from pytanga.basis import BasisP3
from pytanga.geometry import Line

p3 = BasisP3()
a = p3("e1 + e4")      # point (1, 0, 0)
b = p3("3 e1 + e4")    # point (3, 0, 0)

line = Line.from_points(a, b)
print(line)            # Line(org=Point(1.00, 0.00, 0.00), dir=Dir(2.00, 0.00, 0.00))
```

The direction is `end - start` and `length` is set to the segment length, so
the visualizer draws exactly the segment.

### `Plane.from_corner_and_span` / `Plane.from_center_and_half_span`

These accept `Point`/`Direction` fields and coerce MVs the same way:

```python
from pytanga.geometry import Plane

u = p3("e1")           # direction (1, 0, 0)
v = p3("e2")           # direction (0, 1, 0)
plane = Plane.from_corner_and_span(a, u, v)
```

## Round-trip example

```python
from pytanga.basis import BasisN3
from pytanga.geometry import Geometry, Point, Sphere

n3 = BasisN3()
geo = Geometry(n3)

# Create a sphere MV, then recover it as a Sphere entity
sphere = Sphere(center=Point(1, 0, 0), radius=3.0)
mv = geo.create(sphere)
recovered = Sphere(mv)

print(recovered.center)   # Point(1.00, 0.00, 0.00)
print(recovered.radius)   # 3.0
```

## Mismatched MVs raise an error

If an MV does not represent the requested entity type, the underlying typed
analyzer raises `ValueError` (or an `analyze_*`-specific exception).  For
example, passing a bivector that is not a simple blade into `Line(mv)` will
fail:

```python
Line(not_a_line_mv)   # raises ValueError
```

## See also

- [Entities](entities.md) — regular field-based construction.
- [Analysis pipeline](analysis.md) — the typed analyzers behind the conversion.
- [`Geometry.__call__`](create.md#geometry__call__) — the dual of this feature:
  convert an entity to an MV or an MV to an entity in one call.