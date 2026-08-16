# Phase 8 — Update Documentation

**Prerequisites:** Phases 1–7 (library, tests, and examples are final).

**Goal:** Update all documentation to the new API: `opns` is an algebra property,
`analyze_*`/`create_*` no longer take `opns`, entity constructors accept MVs, and the
visualizer no longer has an `opns` parameter.

---

## 1. Files to update

Based on the current `opns` occurrences in `docs/`:

| File | Change |
|------|--------|
| `docs/py/geometry/create.md` | Remove `opns=` kwargs; document `Algebra(opns=False)` / `alg.opns`. Show `create(algebra, obj)` and `create_entity`. |
| `docs/py/geometry/analysis.md` | `analyze_entity(mv)` / `analyze(mv)` no `opns`; document typed analyzers (`analyze_point`, `analyze_direction`, …) and MV-accepting entity constructors. |
| `docs/py/geometry/round-trip.md` | `Geometry(algebra)` — no `opns`; flag comes from the algebra. |
| `docs/py/viz/visualizer.md` | Remove the `opns` constructor column and `add(..., opns=...)`; note that MVs carry the flag from their algebra. |
| `docs/py/viz/interactive.md` | Remove `opns=True` from `Visualizer(...)` examples. |

Any other file matching `rg "opns" docs/` is reviewed and updated or explicitly
left as a mention of the algebra flag.

---

## 2. Content to add / clarify

- **`Algebra.opns` (mutable)** — explain that it is the single source of truth for
  OPNS/IPNS interpretation, that `mv.opns` delegates to it, and that mutating it
  reinterprets subsequently analyzed MVs.
- **`Basis*(opns=False)`** — construct an IPNS algebra directly.
- **Typed analyzers** — one short table of `analyze_point` / `analyze_direction`
  / … availability per algebra (reuse the Phase 2 matrix).
- **MV-accepting entity constructors** — `Point(mv)`, `Direction(mv)`, `Line(mv)`,
  `Plane(mv)`, `Circle(mv)`, `Sphere(mv)`, `Space(mv)`, `PointPair(mv)`,
  `HPoint(mv)`, `HDirection(mv)`; note the E3-vector convenience and that a
  mismatched MV raises.
- **Auto-conversion conveniences** — `Geometry.__call__` (`A = geo(Point(1, 2, 3))`),
  entity constructors (`Circle(point_mv, radius_mv, normal_mv)` for point/scalar/
  direction MVs), `Line.from_points(mv, mv)`, and `PointPath.add(mv)`.
- **Visualizer** — `Visualizer()` no longer takes `opns`; entity MVs must be
  produced by an algebra with the desired flag.
- **Geometry is created only via the `geometry` submodule** — basis classes no
  longer carry `point`/`direction`/`line`/`plane`/`vector`/`rotor` methods; show
  `create(...)`/`create_entity(...)`/`geo(...)` in place of `basis.point(...)` etc.

---

## 3. Docstring consistency (library)

As part of the final consolidation, ensure no library docstring still references an
`opns` **parameter** (the flag is still mentioned as an algebra attribute). Grep
`rg "opns" py/pytanga` and update stale docstrings introduced in earlier phases.

---

## 4. Implementation Checklist

- [ ] Update `docs/py/geometry/create.md`
- [ ] Update `docs/py/geometry/analysis.md`
- [ ] Update `docs/py/geometry/round-trip.md`
- [ ] Update `docs/py/viz/visualizer.md`
- [ ] Update `docs/py/viz/interactive.md`
- [ ] Remove/adjust any docs showing basis geometry methods (`basis.point(...)`, etc.)
- [ ] Grep `rg "opns" docs/` → no stale `opns=` API examples
- [ ] Grep `rg "opns" py/pytanga` → no stale `opns` **parameter** in docstrings
- [ ] Document `Geometry.__call__`, `Line.from_points(mv, mv)`, `PointPath.add(mv)`

---

## 5. Verification

- [ ] Docs build cleanly (`mkdocs build` or `mkdocs serve` smoke check)
- [ ] All code snippets in docs reflect the new API
- [ ] `opns` is documented solely as an algebra property (no per-call parameter)
- [ ] `Geometry.__call__`, entity constructors, and `PointPath.add` are documented
