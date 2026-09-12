# Phase 4 — Demos: quadric3d + effective-rotor visualization

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`, in particular
> `viz-architecture.md` and `viz-controls-and-interactions.md`) for the
> subsystem(s) this work touches, so the new code aligns with the documented
> architecture.  If this work introduces or changes architecture, update the
> developer docs.

## Goal

Add `quadric3d_demo.py` (9 points, 3 action points, three rotor sliders) and add
"effective rotor" visualization to both demos.

## Files

- New: `py/examples/ga/quadric/quadric3d_demo.py`
- Edit: `py/examples/ga/quadric/conic_demo.py`

## Steps

- [x] **4.1 — `quadric3d_demo.py` (structure)**
  - Follow `example-docs.md`: license header + docstring (one-liner, `Run with:`,
    `Keywords:` incl. `quadric, quadric3d, rotor, slider`).  Note in the docstring
    the 9-points/3-action-points dof argument (3 action points reach an open dense
    set of quadrics).
  - `Q3 = BasisQ3(opns=True)`, `geo = Geometry(Q3)`; six fixed points plus three
    `ActPoint`s on an ellipsoid (no four coplanar / no degeneracy).
  - Reconstruct the quadric as the grade-9 join `p1 ^ p2 ^ … ^ p6 ^ geo(ap1) ^
    geo(ap2) ^ geo(ap3)`; `viz.new(quadric)` resolves it to a `Quadric3D`/refined
    entity (mirror `conic_demo.py`).
- [x] **4.2 — Three rotor sliders (axis 2× + angle 1×)**
  - Two `SliderView`s for the axis spherical angles (azimuth 0–360°, polar 0–180°)
    and one for the rotation angle (−180–180°).
  - `on_change` computes `axis = (sinφ·cosθ, sinφ·sinθ, cosφ)` and builds
    `rotor = geo(Rotor(radians(angle), Direction(*axis)))`; store the base quadric
    and apply `rotor.vp(base)` to the displayed entity (reuse the `conic_demo`
    pattern with `global` state or a small closure).
- [x] **4.3 — Visualize the effective rotor (both demos)**
  - `eff = analyze_operator(rotor)` → `Rotor(angle, axis)`; `viz.add(eff, …)` (or
    update an existing rotor entity) so the operator renderer shows axis + arc.
  - `conic_demo.py`: add the same for its single angle slider (axis `Dir(0,0,1)`);
    verify the operator renderer works in `space_dim=2`; if it does not, fall back
    to an annotation/arc (note the decision).
- [x] **4.4 — Sliders wiring + layout**
  - `viz.set_layout(SceneView("", overlay=[GroupView("Rotation", [...], …)]))`
    (matches `ui/controls/control_group_single.py`); handlers `viz.flush()`.
- [x] **4.5 — Example docs**
  - `uv run python tools/generate-example-docs.py` (then `--check`).

## Validation

`uv run python -m py_compile py/examples/ga/quadric/quadric3d_demo.py && uv run python tools/generate-example-docs.py --check`

## Notes

- Reuse the existing operator renderer (`viz.add(Rotor(...))`) — no new frontend.
- Keep the two demos parallel in style so the quadric3d demo reads as the 3D
  counterpart of the conic demo.
