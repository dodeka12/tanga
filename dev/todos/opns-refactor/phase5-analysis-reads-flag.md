# Phase 5 — Analysis Path Reads `mv.algebra.opns`

**Prerequisites:** Phase 4.

**Goal:** Remove the `opns` keyword from the analysis path and make it read
`mv.algebra.opns`. Bundle all direct callers (`Geometry.which_entity`, `Geometry.analyze`,
`Geometry._opns`, the visualizer, and `_point_path`) in the same phase so no caller
still passes a stale `opns=` argument.

---

## 1. `analysis_*` modules

For each of the 8 `analysis_*` modules:

- Change `def analyze_entity(mv, *, opns: bool = True)` → `def analyze_entity(mv)`.
- Replace the `if not opns:` branch with `if not mv.algebra.opns:`.

Files: `analysis_e2.py`, `analysis_e3.py`, `analysis_p2.py`, `analysis_p3.py`,
`analysis_n2.py`, `analysis_n3.py`, `analysis_pga2.py`, `analysis_pga3.py`.

Typed analyzers added in Phase 2 that temporarily called
`analyze_entity(mv, opns=mv.algebra.opns)` are updated here to `analyze_entity(mv)`.

---

## 2. `analysis.py` dispatcher

- `analyze_entity(mv, *, opns: bool = True)` → `analyze_entity(mv)`; drop the
  `opns=opns` forwarding to each module.
- `analyze(mv, *, opns: bool = True)` → `analyze(mv)`; the `try` block calls
  `analyze_entity(mv)`.
- Re-export the typed analyzers (Phase 2) from `__init__.py` as needed; the shared
  dispatcher functions `analyze_point/analyze_direction/…` (added in Phase 2) already
  call the per-algebra module functions directly.

---

## 3. `geometry/_geometry.py` — `Geometry`

- Remove `opns` from `__init__`; change `__slots__` to `("_algebra",)`.
- `which_entity(mv, *, opns=None)` → `which_entity(mv)` → `analyze_entity(mv)`.
- `analyze(mv, *, opns=None)` → `analyze(mv)` → `_analyze(mv)`.
- Delete `_opns()`.

`which_operator` already takes no `opns`; unchanged.

---

## 4. Viz callers

- `py/pytanga/viz/visualizer.py`:
  - Remove `opns` from `__init__`; drop `self._opns`.
  - Remove `opns` from `add()`, `_add_to_scene()`, `update_entity()`.
  - `_resolve(obj, *, opns=True)` → `_resolve(obj)` → `analyze(obj)`.
- `py/pytanga/viz/_scene_handle.py`: remove `opns` from `add()`, `update_entity()`;
  stop reading `self._viz._opns`.
- `py/pytanga/viz/_app.py`: remove the `opns` param and its forwarding.
- `py/pytanga/viz/_point_path.py`: `PointPath.add` calls `analyze(point)`; change it
  to use the typed entity conversion directly — treat an MV argument as
  `GeoPoint(point)`, falling back to `HPoint`/`Sphere.center` exactly as today but
  through the typed constructors (see §5). This reuses Phase 3's `Point(mv)` instead
  of the generic `analyze` dispatcher, keeping the auto-conversion contract explicit.

---

## 5. `PointPath.add` MV auto-conversion

In `py/pytanga/viz/_point_path.py`, update `_resolve_point(point)`:

```python
def _resolve_point(point):
    if hasattr(point, "_alg"):
        from pytanga.geometry.entities import HPoint, Point as GeoPoint, Sphere
        result = GeoPoint(point)          # typed conversion; raises on mismatch
        return (result.x, result.y, result.z)
    ...
```

If preserving the old fallback compatibility (an MV resolving to `HPoint` /
`Sphere` center) is desired, keep a two-step try:

```python
def _resolve_point(point):
    if hasattr(point, "_alg"):
        from pytanga.geometry import analyze
        from pytanga.geometry.entities import HPoint, Point as GeoPoint, Sphere
        result = analyze(point)           # reads mv.algebra.opns (after Phase 4)
        ...
```

Decision: use the **typed** `GeoPoint(point)` for `PointPath.add` (the path is a
list of explicit points); the generic `analyze` compatibility (HPoint/Sphere center)
can remain as a fallback if tests require it. Either way, after Phase 4 remove any
`opns=` argument from the `analyze` call (it already takes none).

---

## 6. Tests (Phase 5)

Update existing tests that call the analysis path with `opns=`:

- `py/tests/geometry/test_geometry_e3_analysis.py`
- `py/tests/geometry/test_geometry_e2_analysis.py`
- `py/tests/geometry/test_geometry_p3_analysis.py`
- `py/tests/geometry/test_geometry_p2_analysis.py`
- `py/tests/geometry/test_geometry_pga3_analysis.py`
- `py/tests/geometry/test_geometry_pga2_analysis.py`
- `py/tests/geometry/test_geometry_n3_analysis.py`
- `py/tests/geometry/test_geometry_n2_analysis.py`
- `py/tests/geometry/test_geometry_e3.py`, `e2.py`, `p3.py`, `p2.py`, `n3.py`,
  `n2.py`, `pga3.py`, `pga2.py` (any `analyze_*(..., opns=...)` calls)
- `py/tests/geometry/test_geometry_convenience.py` (Geometry `opns` tests — rewrite
  to assert delegation: `Geometry(b).which_entity` follows `b.opns`)
- `py/tests/viz/test_scene_session.py` (asserts `viz._opns is True` → remove/replace)
- `py/tests/viz/test_point_path.py` (if present) — `PointPath.add(mv)` now uses the
  typed conversion; update/verify.

Mechanical rewrite: replace `analyze_entity(mv, opns=False)` with a fixture/context
that sets `alg.opns = False` before the call, and drop `opns=True` arguments.

---

## 7. Implementation Checklist

- [ ] Remove `opns` from 8 `analysis_*` module `analyze_entity`
- [ ] Remove `opns` from `analysis.py` `analyze_entity`/`analyze`
- [ ] Update Phase-2 typed analyzers that referenced the old `opns=` argument
- [ ] Remove `opns` from `Geometry` (store/slots/`which_entity`/`analyze`/`_opns`)
- [ ] Remove `opns` from `viz/visualizer.py`, `_scene_handle.py`, `_app.py`
- [ ] Update `_point_path.py` `_resolve_point` to typed conversion (drop `opns`)
- [ ] Update the test files listed above (set `alg.opns` where IPNS is tested)
- [ ] Run: `pytest py/tests/geometry py/tests/viz -q`

---

## 8. Verification

- [ ] `analyze_entity(mv)` / `analyze(mv)` no longer accept `opns`
- [ ] `Geometry.which_entity(mv)` / `Geometry.analyze(mv)` follow `algebra.opns`
- [ ] `viz.add(mv)` resolves via the MV's algebra flag
- [ ] `PointPath.add(mv)` auto-converts a point MV and raises on mismatch
- [ ] Full geometry + viz test suites pass
