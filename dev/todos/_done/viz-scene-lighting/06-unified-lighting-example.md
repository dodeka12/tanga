# Phase 6 — Unified lighting demo example

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/architecture/viz-architecture.md` (scene lighting) and the controls
> doc `docs/dev/architecture/viz-controls-and-interactions.md`.  This example
> only *uses* existing controls (no new control/view), so it adds no
> architecture; follow `dev/workflows/example-docs.md` for the docstring header.

## Goal

Add a standalone example that proves the per-scene lighting config lights
**three different rendering paths identically**: a mesh sphere (standard
`MeshPhongMaterial`), an SDF cylinder (ray-marched), and a 2.5D depth surface of
a 2D sine wave (custom depth shader, plain mode) — and shows how to change the
lighting at runtime via `Visualizer.set_scene_lighting`.

## Files

- **New** `py/examples/viz/lighting/scene_lighting.py`.
- **Edit** `py/pytanga/viz/templates/renderers/sdf.js` — add `applySdfProxyLighting`.
- **Edit** `py/pytanga/viz/templates/renderers/depth-image.js` — add
  `applyDepthImageLighting`.
- **Edit** `py/pytanga/viz/templates/views/three-view.js` — `_applyShaderLighting`
  (re-lights SDF + depth shaders from the scene config; closes the
  scene-config plumbing deferred in phase 5).

## Steps

- [x] 6.1 Create `py/examples/viz/lighting/scene_lighting.py` with the standard
  license header + a docstring in the `<name>.py — …` form, a `Run with:  uv run
  python py/examples/viz/lighting/scene_lighting.py` line, and a `Keywords:`
  line (e.g. `Keywords: scene lighting, SDF, depth image, sphere, cylinder, mesh`).
- [x] 6.2 Build the three objects and add them (before `show()`):
  - **mesh sphere** — `Sphere(Point(-3, 0, 0), 1.0)` via
    `viz.add(..., color="…")` (standard vertex/mesh pipeline).
  - **SDF cylinder** — `SdfObject(Cylinder(origin=Point(0, 0, 0),
    axis=Direction(0, 0, 1), length=2.0, radius=0.6, align_center=0.5),
    style=SdfCylinderStyle(color="…"))` via `viz.add(...)`.
  - **depth sine wave** — build a normalized `np.ndarray` depth map
    (`(sin(2π·f1·u + φ1) · sin(2π·f2·v + φ2) + 1) / 2`, mirroring
    `depth_surface.py`) and add `DepthImage(DepthImageData(depth=depth))` with
    `DepthImageStyle(render_mode="plain", color="…", world_scale=…,
    depth_scale=…)` so its plain mode is lit.
- [x] 6.3 Define 3–4 `SceneLighting` presets (e.g. `default`, `warm`, `cool`,
  `single top`, `dramatic side`) using `LightSpec` / `DirectionalLightSpec`, and
  a `DropdownView("lighting", options=[…], value="default")` whose change
  handler calls `viz.set_scene_lighting(preset)` (and `viz.flush()` if needed).
  This is the "how to change lighting" demonstration.
- [x] 6.4 Lay it out with `SplitView` (a `GroupView` of the lighting control +
  a `SceneView("")`) and `viz.show(layout=…)` / `viz.wait()`, matching
  `depth_surface.py`'s structure.  Use `add_default_grid=False`.
- [x] 6.5 Smoke-run the example manually: confirm the sphere, cylinder, and
  depth surface all respond to the same lighting preset (same bright/dark sides,
  same ambient), and that switching presets re-lights all three at once.

## Validation

```bash
uv run python -m py_compile py/examples/viz/lighting/scene_lighting.py
# Manual smoke (blocking viewer — close browser / Ctrl+C to exit):
uv run python py/examples/viz/lighting/scene_lighting.py
```
