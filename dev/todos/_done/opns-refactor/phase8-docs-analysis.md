# Phase 8a — Documentation File Analysis

Per-file scan of every Markdown file under `docs/` for Phase 8
(update documentation to the new API: `opns` is an algebra property, no
`opns=` keyword arguments remain, and the Phase 4-removed basis geometry
factories no longer appear). Each entry lists keywords found and what,
if anything, needs changing.

Legend for the two change categories:

- **`opns=` kwargs / stale wording** — `Geometry(alg, opns=...)`,
  `create/algebra(..., opns=...)`, `analyze_entity(..., opns=...)`,
  `Visualizer(opns=...)`, `add(..., opns=...)` must be removed; document
  `Algebra(opns=False)` / `alg.opns` as the single source of truth.
- **Removed basis factories** — Phase 4 removed `point`, `direction`,
  `line`, `plane`, `vector`, `rnd_vector`, `rnd_point`, `rnd_direction`,
  `rotor` from the `Basis*` classes. Replace with `geometry.create_entity` /
  `geometry.create_operator` / typed entities / string conversion (`E3("…")`).

---

## `docs/py/index.md`

- **Keywords:** `v = E3.vector(1, 2, 3)`, `w = E3.vector(0, 1, 0)` — **removed**.
- **Changes:** replace with `E3("e1 + 2 e2 + 3 e3")` / `E3("e2")` (string
  conversion) or `geometry.create_entity`.

---

## `docs/py/basis/`

### `basis/index.md`

- **Keywords:** `v = E3.vector(1, 2, 3)` — **removed**.
- **Changes:** replace with string conversion (`E3("e1 + 2 e2 + 3 e3")`).

### `basis/bases.md`

- **Keywords:** numerous removed factories across all eight bases:
  `E3.vector`, `P3.point`, `E2.vector`/`E2.rnd_vector`/`E2.rotor`,
  `P2.point`/`P2.direction`/`P2.rnd_point`/`P2.rnd_direction`,
  `pga.point`/`pga.direction`/`pga.plane`, `pga2.point`/`pga2.direction`/
  `pga2.line`, and `v = E3.vector(1, 2, 3)` in the "Pattern 2" section.
- **Changes:** replace each "Factory methods" block. For raw basis demos use
  string conversion (e.g. `P3("e1 + e4")`, `pga("e1 + e2 + e3 + e0")`);
  for geometric intent, point to `geometry.create_entity` /
  `geometry.create_operator`. The PGA3/PGA2 `einf`/`eo` notes are already
  correct (no change there).

### `basis/basis_e2.md`

- **Keywords:** `E2.vector(3, 4)`, `E2.rotor(1.57, E2.e12)`,
  `E2.vector(1, 0)`, `E2.vector(0, 1)`, `E2.rotor(math.pi / 2, E2.e12)` —
  **removed**.
- **Changes:** vectors via string conversion; rotors via
  `geometry.create_operator(E2, Rotor(...))` (or the `geometry.create_e2`
  path). The `R * a * ~R` demonstration stays but `R` must come from `geometry`.

### `basis/basis_p2.md`

- **Keywords:** `P2.point(3, 4)`, `P2.direction(1, 0)`, `P2.rnd_point(...)`,
  `P2.rnd_direction(...)`, `P2.point(2, 3)`, `P2.direction(1, 1)`,
  `P2.point(5, 1)` — **removed**.
- **Changes:** replace with `geometry.create_entity(P2, Point(...))` /
  `Direction(...)`; randomness via `P2.rng.uniform(...)`. `P2.op(...)` and
  `P2.show(...)` remain valid.

### `basis/basis_pga2.md`

- **Keywords:** `pga2.point(3, 4)`, `pga2.direction(1, 0)`,
  `pga2.line(nx=1, ny=0, d=2)`, `line_x`/`line_y`, `pga2.point(2, 3)` —
  **removed**.
- **Changes:** replace with `geometry.create_entity(pga2, Point/Direction/Line(...))`
  or raw `pga2("...")`; keep the grade tables and the correct `e0`/`e0_inv`
  naming (already correct).

### `basis/basis_pga3.md`

- **Keywords:** `pga.point(3, 4, 5)`, `pga.direction(1, 0, 0)`,
  `pga.plane(0, 0, 1, 3)` — **removed**.
- **Changes:** replace with `geometry.create_entity(pga, Point/Direction/Plane(...))`
  or raw `pga("...")`.

### `basis/basis_n2.md`, `basis/basis_n3.md`, `basis/pga_null_embedding.md`

- **Keywords:** raw null-vector naming only (`einf`, `eo`, `ep`, `em`).
- **Changes:** none. Correct as-is.

---

## `docs/py/geometry/`

### `geometry/index.md`

- **Keywords:** `point_mv = e3.vector(1, 2, 3)`, `rotor_mv = e3.rotor(1.57, e3.e3)` — **removed**.
- **Changes:** `e3.vector(...)` → `e3("e1 + 2 e2 + 3 e3")`;
  `e3.rotor(...)` → `geometry.create_operator(e3, Rotor(angle=..., axis=Direction(...)))`.

### `geometry/create.md`

- **Keywords:** `Geometry(n3, opns=True)`, `geo.create(..., opns=False)`,
  `Geometry(n3, opns=False)`, `create(algebra, obj, opns=True)`,
  `create_entity(algebra, entity, opns=True)` — **`opns=` kwargs**.
- **Changes:**
  - "OPNS / IPNS" section → show `n3 = BasisN3(opns=False)` or
    `n3.opns = False`, then `geo = Geometry(n3)`.
  - Plain functions → `create(algebra, obj)`, `create_entity(algebra, entity)`,
    `create_operator(algebra, operator)` (no `opns`).
  - Add `Algebra.opns` note and `Geometry.__call__` (`geo(Point(...))`).
  - The `create.md` "Unsupported" section and the entity-representation table
    are otherwise correct (N3 uses `einf`/`eo`, PGA3 uses `e₀` — verify naming).

### `geometry/analysis.md`

- **Keywords:** `e3.vector(1, 2, 3)`, `e3.rotor(1.57, e3.e3)`,
  `analyze_entity(mv, opns=True)` — **removed / `opns=` kwarg**.
- **Changes:** `e3.vector(...)` → string conversion; `e3.rotor(...)` →
  `geometry.create_operator`; plain functions → `analyze_entity(mv)` (no `opns`).
  Add typed analyzers (`analyze_point`, `analyze_direction`, …) and
  MV-accepting entity constructors per Phase 8 plan.

### `geometry/round-trip.md`

- **Keywords:** `Geometry(algebra, opns=True)` — **`opns=` kwarg**; stale
  wording in "Plain Functions" ("pass … OPNS flag explicitly on each call",
  "stores the algebra and default OPNS flag").
- **Changes:** `Geometry(algebra)` (flag comes from the algebra). Reword the
  "Plain Functions" prose and the closing paragraph to state that the flag
  lives on the algebra, not on the `Geometry` wrapper.

### `geometry/entities.md`

- **Keywords:** `e3.vector(3, 4, 5)`, `e3.vector(1, 2, 3)`,
  `e3.vector(Point(1, 2, 3))`, `e3.vector(Direction(1, 0, 0))` — **removed**.
- **Changes:** construct the MV via string conversion (`e3("3 e1 + 4 e2 + 5 e3")`)
  before passing to `Point(mv)`/`Direction(mv)`. Keep the MV-accepting
  constructor documentation (its semantics are correct).

### `geometry/operators.md`

- **Keywords:** none matching removed factories or `opns=`. (Verify only.)
- **Changes:** none expected.

---

## `docs/py/viz/`

### `viz/visualizer.md`

- **Keywords:** `opns=True` in the `Visualizer(...)` constructor; the
  `| opns | bool | True | Default MV interpretation (OPNS/IPNS) |` table row;
  `add(..., opns=None, ...)`; `viz = Visualizer(opns=True)`;
  `viz.add(pga.point(5, 0, 0), ...)`, `viz.add(..., opns=False)`,
  `viz.add(pga.plane(0, 0, 1, 3), ...)`; the "The opns flag on add()
  overrides the instance default …" paragraph — **`opns=` kwarg + removed factories**.
- **Changes:**
  - Remove `opns=True` from the constructor call and the `opns` table row.
  - Remove `opns=None` from the `add()` signature example.
  - Rewrite the "MV Input" example to build MVs via `Geometry`/`create_entity`
    with an IPNS algebra (`BasisPGA3(opns=False)`), and note that MVs carry
    the interpretation from their algebra.

### `viz/interactive.md`

- **Keywords:** `opns=True` in the `VisualizerApp(...)` constructor example — **`opns=` kwarg**.
- **Changes:** remove `opns=True`; note the flag is set on the algebra.

### `viz/point-path.md`

- **Keywords:** `PointPath` / `PointPath.add` (correct API).
- **Changes:** none. (Optionally document `PointPath.add(mv)` auto-conversion
  per the Phase 8 plan.)

### Other viz docs (`camera.md`, `axes-grid.md`, `animation.md`, `export.md`,
`jupyter.md`, `labels.md`, `object-interaction.md`, `styles.md`,
`texture-labels.md`, `title-annotation.md`, `active-elements/*`)

- **Keywords:** no `opns=` kwargs or removed basis factories found.
- **Changes:** none.

---

## `docs/cpp/`, `docs/dev/`, `docs/changelog/`, `docs/javascripts/`, `docs/overrides/`

- **Keywords:** `docs/changelog/2026-08-16_7cb2db1.md` and
  `docs/changelog/index.md` correctly document the breaking changes and the
  updated examples (historical/correct — leave as-is).
- **Changes:** none.

---

## Summary

| Category | Files |
|----------|-------|
| `opns=` kwargs / stale wording | `geometry/create.md`, `geometry/analysis.md`, `geometry/round-trip.md`, `viz/visualizer.md`, `viz/interactive.md` |
| Removed basis factories | `py/index.md`, `basis/index.md`, `basis/bases.md`, `basis/basis_e2.md`, `basis/basis_p2.md`, `basis/basis_pga2.md`, `basis/basis_pga3.md`, `geometry/index.md`, `geometry/analysis.md`, `geometry/entities.md`, `viz/visualizer.md` |
| Both | `geometry/analysis.md`, `viz/visualizer.md` |
| No change | all other `docs/` files (basis_n2/n3, pga_null_embedding, geometry/operators, most viz docs, cpp/, dev/, changelog/) |

After the Phase 8 edits:
- `rg "opns" docs/` must return only algebra-property mentions and changelog/historical text (no `opns=` API examples).
- `rg "(point|direction|line|plane|vector|rotor|rnd_)" docs/` must not show basis-method examples in the `Basis*` sections.