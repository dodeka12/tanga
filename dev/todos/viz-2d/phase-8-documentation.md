# Phase 8 — Documentation

User‑facing documentation for 2D algebras and the 2D viewer mode. Update
existing `docs/py/` pages and add new basis class docs.

## Files to Create

### `docs/py/basis/basis_e2.md`

Document the `BasisE2` class:

- `Algebra.from_name("E2")` usage
- Named blades: `e1`, `e2`, `e12` (pseudoscalar `I`)
- Methods: `vector(x, y)`, `rnd_vector(x_range, y_range)`, `rotor(theta, axis)`
- Example: creating and displaying vectors/bivectors
- Note: E2 cannot represent points — use P2 or N2 for points

### `docs/py/basis/basis_p2.md`

Document the `BasisP2` class:

- `Algebra.from_name("P2")` usage
- Projective 2D: homogeneous coordinate `e3`
- Named blades: `e1`, `e2`, `e3`, `e123`
- Methods: `point(x, y)`, `direction(x, y)`, `rnd_point()`, `rnd_direction()`, `rotor(theta, axis)`
- Example: adding points and lines in P2, homogeneous transforms

### `docs/py/basis/basis_n2.md`

Document the `BasisN2` class:

- `Algebra.from_name("N2")` usage
- Conformal 2D: null embedding with `einf = ep + em`, `eo = −0.5·ep + 0.5·em`
- Named blades: `e1`, `e2`, `ep`, `em`, composed `einf`, `eo`
- Display basis with null swap for readable output
- Example: conformal point, sphere as circle, translations in 2D

### `docs/py/basis/basis_pga2.md`

Document the `BasisPGA2` class:

- `Algebra.from_name("PGA2")` usage
- Gunn/Dorst plane‑based PGA for 2D, null vector `e0` via ep+em embedding
- Named blades: `e1`, `e2`, `e0`, `e0_inv`
- Methods: `point(x, y)`, `direction(x, y)`, `plane(nx, ny, d)`
- Example: PGA2 planes as 2D lines, point intersection of two lines

## Files to Modify

### `docs/py/basis/bases.md`

Add 2D basis classes to the overview:

| Name | Description | dim | sig | Key Use |
|------|-------------|-----|-----|---------|
| E2 | Euclidean 2D | 2 | 0 | Vectors, bivectors, rotors |
| P2 | Projective 2D | 3 | 0 | Points, lines (homogeneous) |
| N2 | Conformal 2D | 4 | 0b1000 | Points, circles, translations, dilations |
| PGA2 | Plane‑based PGA 2D | 4 | 0b1000 | Points, lines (plane intersection) |

Link each row to the appropriate detail page.

### `docs/py/basis/index.md`

Add 2D basis classes to the navigation table / list.

### `docs/py/basis/pga_null_embedding.md`

Mention that the null vector embedding applies to both PGA3 and PGA2:
- PGA3: `e0 = ep + em` with `ep²=+1, em²=−1` in G(5, 0b10000)
- PGA2: `e0 = ep + em` with `ep²=+1, em²=−1` in G(4, 0b1000)

### `docs/py/geometry/entities.md`

Add a note that entities are dimension‑agnostic:

> When working with 2D algebras (E2, P2, N2, PGA2), all entities still use
> 3D data fields. The `z` component is always 0. For example, `Point(3, 4, 0)`
> represents the point at (3, 4) in 2D space.

### `docs/py/geometry/operators.md`

Same note for operators:

> 2D operators use the same classes. `Rotor(angle, Direction(0, 0, 1))`
> always rotates in the XY plane — the only rotation plane in 2D.

### `docs/py/geometry/round-trip.md`

Add 2D round‑trip examples:

```python
from pytanga.algebra import Algebra
from pytanga.geometry import Geometry, Point, Direction, Rotor

# E2: directions and rotors
geo = Geometry(Algebra.from_name("E2"))
d = geo.create(Direction(3, 4, 0))
assert isinstance(geo.which_entity(d), Direction)

# N2: points, lines, spheres (circles in 2D)
geo = Geometry(Algebra.from_name("N2"))
p = geo.create(Point(1, 2, 0))
assert isinstance(geo.which_entity(p), Point)

r = Rotor(1.57, Direction(0, 0, 1))
mv = geo.create(r)
assert isinstance(geo.which_operator(mv), Rotor)
```

### `docs/py/viz/visualizer.md`

Document the `space_dim` parameter:

- Add `space_dim` to constructor parameter table
- Add a "2D Visualization" subsection:
  - Activate with `Visualizer(space_dim=2)`
  - Default title becomes `"Tanga 2D Viewer"`
  - Camera switches to orthographic top‑down view
  - Controls: pan (right‑click drag), zoom (scroll wheel), no orbit rotation
  - Grid renders as a flat plane
  - **Full 3D entities render in 2D mode.** Any 3D entity (e.g. `Sphere`,
    `Plane`, `Circle` with non‑zero `z`) can be added and renders correctly
    from the orthographic top‑down perspective. This works out of the box
    with no additional code — the camera change alone handles it.
  - **Z‑coordinate = overlay order:** In 2D mode, the `z` field of entity
    dataclasses controls draw order, not camera depth. Entities with larger
    positive `z` render on top of those with smaller `z` (e.g.
    `Point(3, 4, 10)` appears above `Point(3, 4, 0)`). This uses
    `renderOrder` with `depthTest=false` on the Three.js materials.
  - Example: `viz = Visualizer(space_dim=2); viz.add(Point(3, 4, 0)); viz.run()`

### `docs/py/viz/camera.md`

Document 2D camera behavior:

- When `space_dim=2`, camera defaults to orthographic, looking down from `(0, 0, 20)` toward `(0, 0, 0)`
- `CameraConfig` still works but `fov` is ignored for orthographic cameras
- Auto‑fit uses 2D bounding box (x‑y extent only)

### `docs/py/index.md`

Add a section or update the overview to mention 2D algebras:

> TANGA supports both 2D and 3D geometric algebras. Use `Algebra.from_name("E2")`,
> `"P2"`, `"N2"`, or `"PGA2"` for 2D; `"E3"`, `"P3"`, `"N3"`, or `"PGA3"` for 3D.
> The visualizer supports both modes via `Visualizer(space_dim=2)`.

## Implementation Checklist

- [ ] 8.1  Create `docs/py/basis/basis_e2.md`
- [ ] 8.2  Create `docs/py/basis/basis_p2.md`
- [ ] 8.3  Create `docs/py/basis/basis_n2.md`
- [ ] 8.4  Create `docs/py/basis/basis_pga2.md`
- [ ] 8.5  Update `docs/py/basis/bases.md` — add 2D bases to overview table
- [ ] 8.6  Update `docs/py/basis/index.md` — add 2D entries to navigation
- [ ] 8.7  Update `docs/py/basis/pga_null_embedding.md` — mention PGA2
- [ ] 8.8  Update `docs/py/geometry/entities.md` — add 2D note
- [ ] 8.9  Update `docs/py/geometry/operators.md` — add 2D note
- [ ] 8.10 Update `docs/py/geometry/round-trip.md` — add 2D examples
- [ ] 8.11 Update `docs/py/viz/visualizer.md` — add `space_dim` doc + 2D subsection
- [ ] 8.12 Update `docs/py/viz/camera.md` — document 2D orthographic camera
- [ ] 8.13 Update `docs/py/index.md` — add 2D algebra overview mention