# Fix stale geometry & viz documentation

**Created:** 2026-08-28 | **Status:** Planned

## Goal

Correct the documentation pages that no longer match the current `py/pytanga`
code. The items below were discovered while validating the
`tanga-tutorial` algebra notebooks against the actual API (signatures and
runtime behavior were checked against the source, not against the published
docs).

## Stale documentation (compiled list)

### 1. `Inversion` constructor argument — `docs/py/geometry/operators.md`

- Line 71 shows `Inversion(origin=Point(0, 0, 0))`.
- Actual signature (source `py/pytanga/geometry/operators.py`):
  `Inversion(center: Point, radius: float = 1.0)`.
- `origin=` no longer exists; the kwarg is `center=`, and there is an optional
  `radius` (the inversion sphere radius, default `1.0`).
- Only the `Inversion` example is stale. `Dilator(factor=…, origin=…)` and
  `GeneralRotor(…, origin=…)` are correct — `origin` is their real kwarg.
- The section heading ("Inversion in a sphere centered at the origin") should
  also be updated to mention `center` / `radius`.

### 2. Precompiled binding list — `docs/dev/workflows/precompiled-wheels.md`

- Lines 12 and 29 say "the five common algebras"; the build script actually
  compiles **seven** bindings.
- Lines 44–45 list "E3, P3/PGA3, N3 (float64), E3 modular (int64), and G(10,0)
  sparse (int64)" — omitting **E2** (`(2,0)`) and **P3** (`(4,0)`), and not
  mentioning that E3/P2 and N2/PGA2 share bindings.
- The Directory Layout block (lines ~153–158) shows five files and is missing
  `binding_dim2_sig0_float64` and `binding_dim4_sig0_float64`.
- Source of truth: `tools/build-precompiled.py` `ALGEBRAS` list, which is
  `(2,0)` E2, `(3,0)` E3/P2, `(4,0)` P3, `(4,8)` N2/PGA2, `(5,16)` N3/PGA3
  (float64), plus `(3,0)` int64 (E3 modular) and `(10,0)` int64 (sparse).

### 3. `GeneralRotor` (and `Motor`) viewer rendering — viz docs + changelog

- `docs/py/viz/visualizer/visualizer.md` (operator list), `scene-objects/index.md`,
  `styles/styles.md`, and `sdf-viewer.md` list `GeneralRotor` / `Motor` as
  renderable operators.
- `docs/changelog/2026-08-22_*.md` claims "GeneralRotor now renders …" and
  "Motor renders …".
- Actual behavior (verified): `viz.add(GeneralRotor(...))` — whether passed as
  the entity or as its MV — raises
  `AttributeError: 'GeneralRotor' object has no attribute 'rotor'`.
  A `Motor` entity/MV still renders (its `.rotor` field exists).
- This is a **code bug** (the renderer/serializer assumes a `Motor`-shaped
  `.rotor` attribute on `GeneralRotor`), which in turn makes the above docs and
  changelog claims stale.

### 4. `Geometry` accepts only `BasisXX` classes — `docs/py/geometry/`

- The geometry docs do not state that `Geometry` binds only the eight `BasisXX`
  classes. A generic `Algebra(dim, sig)` constructs a `Geometry`, but
  `create(...)` raises `ValueError: Unknown basis type: Algebra` (source
  `py/pytanga/geometry/create.py:76`) and `analyze(...)` returns `None`.
- This is a documentation gap rather than a code bug; it should be called out on
  the geometry index and/or creation pages.

## Changes

### Phase 1 — `Inversion` doc fix

- [x] 1.1 `docs/py/geometry/operators.md`: change `Inversion(origin=…)` to
      `Inversion(center=…)`, document the optional `radius` (default `1.0`), and
      update the section heading/description.

### Phase 2 — precompiled list fix

- [x] 2.1 `docs/dev/workflows/precompiled-wheels.md`: replace "five" with the
      correct count (seven) and list all seven bindings from
      `tools/build-precompiled.py` (noting the E3/P2 and N2/PGA2 sharing).
- [x] 2.2 Update the Directory Layout block to include
      `binding_dim2_sig0_float64` and `binding_dim4_sig0_float64`.

### Phase 3 — `GeneralRotor` rendering (code fix first, then docs)

- [x] 3.1 Fix the renderer/serializer so `GeneralRotor` renders without
      dereferencing `.rotor` (root cause: the `Motor` screw-form change made
      `Motor.rotor` a `GeneralRotor`, and the `GeneralRotor` render path still
      assumes a `Motor` shape).
- [x] 3.2 N/A — the code fix in 3.1 landed, so the viz docs and the changelog
      claims are accurate again; no "not renderable yet" correction is needed.

### Phase 4 — document the `Geometry` basis-class restriction

- [ ] 4.1 `docs/py/geometry/index.md` and/or `create.md`: add a note that
      `Geometry` only accepts the built-in `BasisXX` classes, and that a generic
      `Algebra` raises `ValueError: Unknown basis type: Algebra` on `create`
      (and `analyze` returns `None`).

## Verification

- [ ] `uv run mkdocs build --strict` — catches broken links and build errors.
- [ ] Spot-check the `Inversion`, precompiled-wheels, and geometry pages render
      with the corrected content.
- [ ] If Phase 3.1 lands: `viz.add(GeneralRotor(...))` no longer raises, and the
      exported snapshot renders the displaced-axis rotor.

## Notes / verified-accurate (no change needed)

- `docs/py/geometry/analysis.md` "Motor vs GeneralRotor | 2+2 vs 2+1 factor
  composition" is correct: `which_operator(Motor)` returns `Motor` when the
  translation has an axial component and `GeneralRotor` when it is perpendicular
  (absorbed into the displaced axis).
- `Dilator(factor=…, origin=…)`, `GeneralRotor(…, origin=…)`, and
  `Line(origin=…)` all use `origin` correctly — only `Inversion` changed to
  `center`.

## Out of scope

- No changes to the `pytanga` public API.
- No changes to `tanga-tutorial` (its notebooks already document the
  `Inversion(center=…)`, precompiled-signature, and `Geometry`-restriction
  behaviors).
