# Phase 6 — Example: hide/show a sphere + its controls

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

A runnable example demonstrating entity hide/show, control hide/show (granular,
no layout re-push), and control disable (grey-out).

## Files

- New: `py/examples/viz/ui/controls/hide_sphere.py`

## Steps

- [x] **6.1 — Header docstring**
  - Follow `dev/workflows/example-docs.md`: license header + module docstring
    (`hide_sphere.py — …` one-liner, `Run with:`, `Keywords:` line).

- [x] **6.2 — Scene + layout**
  - Default scene: `viz.add(Sphere(Point(0, 0, 0), radius=2),
    entity_id="sphere", color="#4488ff", opacity=0.4)`.
  - `SplitView(orientation="horizontal")` with a left `GroupView("Controls", …)`
    and a right `SceneView("")`.

- [x] **6.3 — Controls + handlers**
  - `CheckboxView("show_sphere", label="Show sphere", value=True,
    on_change=_on_show)`.
  - `SliderView("radius", label="Radius", min=0.2, max=5.0, value=2.0,
    on_change=_on_radius)`.
  - `CheckboxView("enable_radius", label="Enable radius", value=True,
    on_change=_on_enable_radius)`.
  - `_on_show`: `viz.set_visible("sphere", bool(value))` +
    `viz.set_control_visible("radius", bool(value))` + `viz.flush()`.
  - `_on_radius`: `viz.update_entity("sphere", Sphere(Point(0, 0, 0),
    radius=float(value)))` + `viz.flush()`.
  - `_on_enable_radius`: `viz.set_control_enabled("radius", bool(value))`.

- [x] **6.4 — Regenerate example docs**
  - `uv run python tools/generate-example-docs.py`.

## Validation

```bash
uv run python tools/generate-example-docs.py --check
```

## Notes

- The radius slider is hidden when the sphere is hidden, demonstrating that a
  single-control state change does not re-push the layout.
