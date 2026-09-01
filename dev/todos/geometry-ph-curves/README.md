# Geometry — Pythagorean-Hodograph Curves — Overview

**Created:** 2026-08-31 | **Status:** Planned | **Branch:** `fix/docs`

## Goal

Add a new *non-multivector* geometric entity — a Pythagorean-hodograph (PH)
curve — plus the supporting reflection primitive, and make PH curves drawable
in the Tanga viewer.

- `PHCurve2D` / `PHCurve3D` — degree-5 (quintic) Hermite interpolants built
  from start/end points and velocities plus a total time, per Perwass
  `PHCurves/hermite.tex` (reflection form). The class pre-computes the curve
  parameter vectors and exposes position / velocity / acceleration /
  tangential & normal acceleration / curvature, for a single time, a list of
  times, and regular interpolation intervals.
- `geometry.reflection.refor` / `reflector` — the Perwass reflector vector and
  a function returning the reflection **line (E2) / plane (E3)** that maps one
  vector into another.
- Viz: a `Colormap` primitive, a `PHCurveStyle` (with `num_points` and an
  optional `colormap`), and serializer support so `viz.add(ph_curve, ...)`
  auto-samples the curve at regular intervals into a `PointPath` (velocity →
  color) and reuses the existing `PointPath` frontend renderer (no JS change).

## Architecture (short)

- `py/pytanga/geometry/reflection.py` (new) — `refor(x, y)` (scaled bisector
  vector, dimension-agnostic numpy) + `reflector(basis, a, b) → MV`.
- `py/pytanga/geometry/phcurve.py` (new) — `_PHCurveBase` + `PHCurve2D` /
  `PHCurve3D`. Pure numpy + `Point`/`Direction`; imports `refor` from
  `reflection.py`.
- `py/pytanga/viz/_colormap.py` (new) — `Colormap` (stops + `map`/`map_values`,
  presets), reusing the hex-lerp helpers already in `viz/_point_path.py`.
- `py/pytanga/viz/_styles/_entity_styles.py` — add `PHCurveStyle`; register it
  in `_styles/__init__.py` `_DEFAULT_STYLE_FOR_KIND` for `PHCurve2D`/`PHCurve3D`.
- `py/pytanga/viz/serializer.py` — `_serialize_ph_curve` + dispatch branches;
  emits `kind: "PointPath"` wire dict so the existing frontend renderer draws it.
- `py/pytanga/viz/_types.py` — add `PHCurve2D`/`PHCurve3D` to `SceneEntity` /
  `VizInputType` so `Visualizer._resolve` passes them through.

Data flow (drawing): `viz.add(PHCurve2D(…), style=PHCurveStyle(num_points=…,
colormap=…))` → `SceneObject(kind="PHCurve2D", data=curve)` →
`serialize_entity` → `_serialize_ph_curve` samples
`curve.positions_regular(n)` + `curve.velocities_regular(n)`, maps speed → hex
colors, and returns `{kind: "PointPath", points, colors, line_thickness, …}`.

## Fixed contract (up front)

### `pytanga.geometry.reflection`

```python
def refor(x, y) -> Direction
    # sqrt(|y|/|x|) * (x̂ + ŷ)/|x̂ + ŷ|  — the Perwass reflector vector
    # (bisector, scaled); y = refor·x·refor in the GA reflection sense.

def reflector(basis, a, b) -> MV
    # E2: grade-1 vector = unit bisector direction (â + b̂)/|â + b̂|
    #     (reflecting across the line it spans maps a → b).
    # E3: grade-2 bivector = n·I⁻¹ with unit normal n = (â − b̂)/|â − b̂|
    #     (same blades as create_e3.create_reflection_plane).
    # a, b: Direction | Point | 3-sequence | MV (grade-1).
    # Raises ValueError for non-E2/E3 bases.
```

### `pytanga.geometry.phcurve`

```python
PHCurve2D(start, end, start_vel, end_vel, total_time, *, nu=None)
PHCurve3D(start, end, start_vel, end_vel, total_time, *, nu=None)
    # start/end: Point; start_vel/end_vel: Direction; total_time: float > 0.
    # nu: optional unit Direction (free parameter); None → auto bisector.

.position(t) -> Point           .positions(times) -> list[Point]
.velocity(t) -> Direction       .velocities(times) -> list[Direction]
.acceleration(t) -> Direction   .accelerations(times) -> list[Direction]
.positions_regular(n) -> list[Point]      .velocities_regular(n) -> list[Direction]
.accelerations_regular(n) -> list[Direction]
.acceleration_along(t) -> Direction            # (a·v̂)v̂
.acceleration_perpendicular(t) -> Direction     # a − a_along
.curvature(t) -> float                          # |a_perp| / |v|²
# each of the three above also has `_times(times)` and `_regular(n)` variants.
```

Pre-computed read-only attributes: `control_points` (6×dim), `hodograph`
(5×dim), `start`, `end`, `start_vel`, `end_vel`, `total_time`, `nu`.

### `pytanga.viz.Colormap` / `PHCurveStyle`

```python
@dataclass(frozen=True)
class Colormap:
    stops: tuple[tuple[float, str], ...]   # normalized, ascending
    def map(self, t: float) -> str
    def map_values(self, values, vmin=None, vmax=None) -> list[str]
    # presets: Colormap.viridis(), Colormap.turbo(), Colormap.coolwarm()

@dataclass
class PHCurveStyle(VizStyle):
    color: str | None = None
    opacity: float | None = None
    line_thickness: float | None = None
    num_points: int | None = None          # default 200
    colormap: Colormap | None = None       # None → uniform color
```

Wire shape emitted by the serializer (reuses `PointPath` renderer):

```json
{"kind": "PointPath", "points": [[x,y,z], …], "colors": ["#rrggbb", …],
 "line_thickness": 2.0, "style": {"style_type": "PointPathStyle", …}}
```

### Math (reflection form, Perwass hermite.tex)

`d0 = T·v0`, `d2 = T·v2`, `Δp = p2 − p0`, `ν` unit. `refor` as above.
`a0 = refor(ν,d0)`, `a2 = refor(ν,d2)`,
`sym(x,y) = (x·ν)y + (y·ν)x − (x·y)ν`, `r02+r20 = 2·sym(a0,a2)`,
`u = 120·Δp − 15(d0+d2) + 10·sym(a0,a2)`, `v = refor(ν,u)`,
`a1 = ¼(v − 3a0 − 3a2)`.
Hodograph quartic Bernstein coefficients:
`c0=d0`, `c1=sym(a0,a1)`,
`c2 = (1/3)sym(a0,a2) + (2/3)(2(a1·ν)a1 − |a1|²ν)`,
`c3=sym(a1,a2)`, `c4=d2`.
Quintic control points: `P0=p0`, `P_{i+1}=P_i + c_i/5`.
Position `R(s)=ΣP_i B_i⁵(s)`, velocity `Σc_i B_i⁴(s)/T`,
acceleration `4Σ(c_{i+1}−c_i)B_i³(s)/T²`.

## Decisions (confirmed)

1. **Reflection form** (not rotation/quaternion form) — dimension-uniform,
   matches the requested `refor` and is simpler/vector-only. Covers "most" PH
   quintics (sufficient for Hermite interpolation).
2. **`nu` auto-chosen** as the bisector of the two end directions, with a
   `nu=` override; degenerate `d0 ≈ −d2` falls back to a perpendicular of `d0`.
3. **Total time** scales normalized data: `d_i = T·v_i` (curve is `R(t/T)`).
4. **Return types** `Point`/`Direction`/`float`; internals numpy.
5. **`reflector` returns a unit** line/plane (isometry mapping `â→b̂`); the
   scaled `refor` stays available for PH construction.
6. **Drawing reuses the `PointPath` frontend renderer** — no JS changes.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-reflection.md](./01-reflection.md) | `reflection.py` (`refor`, `reflector`) + tests |
| 2 | [02-ph-curve-core.md](./02-ph-curve-core.md) | `phcurve.py` (`PHCurve2D`/`PHCurve3D`) + tests |
| 3 | [03-colormap.md](./03-colormap.md) | `viz/_colormap.py` (`Colormap` + presets) + tests |
| 4 | [04-viz-phcurve-drawing.md](./04-viz-phcurve-drawing.md) | `PHCurveStyle`, serializer, `_types` + tests |
| 5 | [05-docs-changelog.md](./05-docs-changelog.md) | docs, example, changelog |

## Testing as you go

- Python: `uv run pytest py/tests/geometry py/tests/viz -q`
- Lint: `uv run ruff check py/pytanga/geometry py/pytanga/viz`
- Docs: `uv run mkdocs build --strict`

## Non-goals

- Rotation (quaternion) PH representation and its `φ_0,φ_1,φ_2` parameters.
- Arc-length reparameterization / exact speed profiles.
- Animated (time-varying) PH curves.
- `Colormap` support for arbitrary external color scales (matplotlib etc.) —
  only the built-in stop-based presets.

