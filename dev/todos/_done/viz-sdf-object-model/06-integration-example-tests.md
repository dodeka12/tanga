# Phase 6 — Integration: examples, regression, browser smoke

## Goal

Exercise the whole object model end-to-end and confirm no regression to the
shipped SDF paths (single-object proxy, fullscreen `SdfVisualizer`, mesh
pipeline). No new machinery here — only examples, tests, and manual checks.

## Files

- New: `py/examples/viz/sdf/object_model.py` (replaces/extends `group.py`).
- Modify: `py/tests/viz/sdf/` additions (if any remain after Phases 1–4).
- No frontend changes (all landed in Phase 5).

## Steps

- [x] **6.1 — Example `py/examples/viz/sdf/object_model.py`**
  - Per-entity styles + `SdfObject` + operators:
    ```python
    left  = SdfObject(Sphere(Point(-1,0,0), 1.0), id="left", style=SdfSphereStyle(color="#ffaa00"))
    drill = SdfObject(Cylinder(...), id="drill", style=SdfCylinderStyle())
    group = left + (drill, ECompose.SUBTRACT)         # or: SdfGroup(left, -drill)
    viz.new(group)
    ```
  - An `SdfGroup` with per-member materials + a member animated by id
    (`sdf_grp.set_member_transform("drill", position=Point(...))`).
  - A `-`/`&`/`^` example showing the operator forms.

- [x] **6.2 — Full Python regression**
  - `uv run pytest py/tests/viz/ -q` and `py/tests/viz/sdf/ -q`.
  - Confirm the marker path, fullscreen `SdfVisualizer`, and mesh pipeline
    tests still pass unchanged.

- [x] **6.3 — JS regression**
  - `node --test 'dev/src/js-tests/*.test.mjs'` + `node dev/src/sdf_proxy_smoke.mjs`.

- [ ] **6.4 — Browser smoke (manual)**
  - `uv run python py/examples/viz/sdf/object_model.py`: sphere + drilled
    cylinder render as one solid; each member shows its own color/opacity; hover
    changes emissive/opacity per member; animated member orbits; the proxy box
    resizes.

- [x] **6.5 — Validate**
  - The three command suites above + the manual browser check.

## Validation

`uv run pytest py/tests/viz/ -q` (green) +
`node dev/src/sdf_proxy_smoke.mjs` (green) +
manual `uv run python py/examples/viz/sdf/object_model.py` (renders correctly).

## Notes

- Keep `py/examples/viz/sdf/objects.py` and `group.py` working (they use the
  legacy marker path and must not break); `object_model.py` demonstrates the new
  API alongside them.
