# Phase 6a — First vertical slice: example script + manual user confirmation

**Status:** Planned

## Goal

Produce the first end-to-end, user-visible proof that the SDF viewer works:
a runnable Python example script that opens the viewer and draws a **Line** and
a **Sphere** defined by the geometry submodule entities (`pytanga.geometry`).
The step ends with **manual user confirmation** in the browser before later
phases build on top of it.

Dependencies (already completed): Phases 1, 2, 4, 5, and 6. This slice is the
gate that validates the analytic entity path (geometry entities, not MVs) before
any algebra/CSG/opacity work begins.

## Files

- New: `py/examples/viz/demo_sdf_entities.py`

## Steps

- [ ] Write `py/examples/viz/demo_sdf_entities.py`:
  - [ ] Construct `Sphere(...)` and `Line(...)` from `pytanga.geometry`.
  - [ ] Add both via `SdfVisualizer.add(...)` (analytic path — no MV objects),
        with distinct colors/styles.
  - [ ] Follow the existing `py/examples/viz/demo_*.py` conventions (module
        docstring, `if __name__ == "__main__"` guard, brief usage comment).
- [ ] Run it with `uv run python py/examples/viz/demo_sdf_entities.py` and
      confirm it launches the `sdf_viewer.html` page in a browser.
- [ ] Wait for **manual user confirmation**: the user visually checks that the
      sphere and line render correctly (shape, position, color, orbit controls),
      and that the sphere is ray-marched and the line is a capped segment.

## Verification

- [ ] `uv run python py/examples/viz/demo_sdf_entities.py` opens the SDF
      viewer and renders a sphere and a line side by side.
- [ ] **Manual confirmation recorded** — the user has visually verified the
      output in the browser (this is a hard stop; later phases are not started
      until confirmation).
- [ ] The example runs without JS console errors / shader compile errors.