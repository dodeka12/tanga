# Phase 7 — Update Example Scripts

**Prerequisites:** Phases 1–6 (library API is final).

**Goal:** Update every example script to the new API: no `opns=` keyword anywhere;
where an IPNS example is demonstrated, set the algebra's `opns` flag (or construct
`Basis*(opns=False)` / `Geometry(algebra)` bound to an IPNS algebra).

---

## 1. Scripts to update

### `py/examples/geometry/`

- `e3_entities.py`
  - `Geometry(e3)` stays (was `Geometry(e3)` default OPNS).
  - `geo.which_entity(vec, opns=False)` → build a separate IPNS view: e.g.
    `geo_ipns = Geometry(BasisE3(opns=False))` and call `geo_ipns.which_entity(vec)`,
    or set `e3.opns = False` / `e3.opns = True` around the section.
  - `geo.create(...)` / `geo.analyze(...)` lose any `opns=` arg.
- `p3_entities.py`
  - `geo.which_entity(mv_p, opns=False)` → IPNS-bound `Geometry` / flag flip.
- `n3_entities.py`
  - `geo.create(sphere, opns=False)`, `geo.which_entity(mv_sp_ipns, opns=False)`,
    `geo.create(Point(5,0,0), opns=False)` → use an IPNS algebra / flag flip.
- `pga3_entities.py`
  - `geo.create(p, opns=False)`, `geo.create(d, opns=False)`,
    `geo.which_entity(mv_d, opns=False)`, `mv_pt = geo.create(Point(3,0,0), opns=False)`.
- `n3_operators.py`
  - `Geometry(n3)` remains; verify no `opns=` in `create`/`analyze` calls.

### `py/examples/viz/`

- `demo_mv_visualization.py`
  - Replace the basis methods `pga.plane`, `pga.point`, `n3.point`, `n3.point_pair`,
    `n3.line_from_origin_direction`, `n3.circle`, `n3.plane`, `n3.sphere`
    (removed in Phase 4) with `geometry.create(...)` / typed entity constructors.
  - `viz.add(pga.point(5,0,0), ..., opns=True, ...)` and `... opns=False ...`
    → create the MV via `geo(Point(5,0,0))` with an IPNS algebra for the
    IPNS variant, and drop the `opns=` args (the MV's algebra carries the flag).
  - `analyze(mv_sphere)` already no `opns` (verify).
- `two_spheres_interact.py`
  - `self._geo = Geometry(b, opns=False)` → `Geometry(BasisN3(opns=False))` (so it
    creates IPNS spheres), then drop all per-call `opns=False` args if any.
  - `viz.add(..., opns=False)` calls → drop the arg; the MV's algebra carries the flag.
- Any other viz script still passing `opns=` via `viz.add(...)` / `update_entity(...)`:
  remove the argument (MVs now carry the flag from their algebra).

### `py/examples/basis/`, `py/examples/numerics/`, `py/examples/tensor/`

- `base_p3_demo.py`, `base_pga3_demo.py`, `solver_point_line_p3.py`,
  `rotor-point-on-ray_01.py` use `P3.point`/`rnd_point`/`rnd_direction`/`rotor`
  (removed in Phase 4) → replace with `geometry.create_entity`/`create_operator`.

---

### New convenience to showcase

- `Geometry.__call__`: prefer `A = geo(Point(1, 2, 3))` over `geo.create(...)` in
  the `*_entities.py` examples where it reads well.
- `Line.from_points(mv_a, mv_b)` and `PointPath.add(mv)` auto-convert multivectors —
  call these out explicitly in a viz demo where MVs would previously have required
  manual analysis.

---

## 2. Mechanical rewrite rules

| Old pattern | New pattern |
|-------------|-------------|
| `Geometry(alg, opns=False)` | `Geometry(BasisX(opns=False))` (or reuse `alg` with `alg.opns = False`) |
| `geo.create(x, opns=False)` | set `geo.algebra.opns = False` (or use an IPNS-bound `Geometry`) |
| `geo.which_entity(mv, opns=False)` | `mv.algebra.opns = False` before the call, or use IPNS algebra |
| `create(alg, obj, opns=False)` | `alg.opns = False; create(alg, obj)` |
| `analyze_entity(mv, opns=False)` | `mv.algebra.opns = False; analyze_entity(mv)` |
| `viz.add(mv, opns=...)` | `viz.add(mv)` (MV's algebra flag is authoritative) |
| `viz = Visualizer(opns=True)` | `viz = Visualizer()` (no `opns` param) |
| `geo.create(x)` (where the example benefits) | `geo(x)` via `Geometry.__call__` |
| `basis.point/direction/line/plane/rotor(...)` | `geometry.create(...)` / `geometry.create_operator(...)` |

---

## 3. No test suite for examples

Examples are not under `py/tests`; they are validated by running them (at minimum,
importing them must not raise a `TypeError: unexpected keyword argument 'opns'`).
A smoke grep for `opns=` should return nothing under `py/examples/` after this phase.

---

## 4. Implementation Checklist

- [ ] Update `py/examples/geometry/*.py`
- [ ] Update `py/examples/viz/*.py`
- [ ] Grep: `rg "opns" py/examples` → only comments/flag usage, no `opns=` kwargs
- [ ] Spot-run import of each updated example (or `python -m py_compile`)
- [ ] Showcase `geo(Point(...))`, `Line.from_points(mv, mv)`, `PointPath.add(mv)`

---

## 5. Verification

- [ ] No `opns=` keyword argument remains in `py/examples/`
- [ ] IPNS examples still show the intended interpretation (via the algebra flag)