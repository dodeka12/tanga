# Depth-image grazing-angle (stretch) filter — Overview

**Created:** 2026-10-20 | **Status:** Done | **Branch:** `fix/image-layers`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/architecture/viz-architecture.md` (the `DepthImage` entity, its
> `uniforms` payload, and the `depth_image_update` granular-message seam) and
> `docs/dev/architecture/viz-controls-and-interactions.md` (the `(id, event)`
> registry + `ControlHandler` shape used by the example slider).  This work adds
> a new uniform and a fragment discard to an existing renderer — it does not add
> a new seam or protocol, so no architecture change is required.

## Goal

Give `DepthImage` a live "depth-jump / grazing-angle" filter that discards the
long, stretched triangles at depth borders (e.g. a car against a wall) while
keeping legitimately slanted surfaces.  The filter is a per-vertex stretch value
computed in the vertex shader and a fragment `discard` against a `u_max_stretch`
threshold, parameterized from Python by `DepthImageStyle(max_grazing_angle=…)`
(degrees).  Runtime changes ride the existing `depth_image_update` channel via
`ref.set_uniform("u_max_stretch", …)` — no rebuild, no pixel re-send.

## Architecture (short)

- **Python** — `DepthImageStyle` gains `max_grazing_angle` (degrees,
  `None` = off).  `DepthImage._serialize_uniforms` converts it to the float
  uniform `u_max_stretch = tan(radians(angle))` (`0.0` = off).
- **Vertex shader** (`depth-shader.js::buildDepthVertex`) already samples `d`,
  `dU`, `dV` and builds `pc`/`pcU`/`pcV` + `nCam`.  It gains `-u`/`-v` samples
  and emits `varying float vStretch` = the max apparent slope over the four
  neighbour pairs.
- **Fragment shader** (`buildDepthFragment`) gains `uniform float u_max_stretch`
  and, between the missing-depth and segment discards,
  `if (u_max_stretch > 0.0 && vStretch > u_max_stretch) discard;`.
- **Renderer** (`depth-image.js::buildDepthUniforms`) registers `u_max_stretch`
  so `applyDepthImageUniforms` (the `depth_image_update` merge) can update it via
  the existing generic float path.
- **Live channel (already exists)** — `VizObjectRef.set_uniform` →
  `Scene.set_depth_image_uniform` → `depth_image_update` → `three-view.js` →
  `applyDepthImageUniforms`.

## Fixed contract (decided up front — later phases implement against this)

1. **API** — `DepthImageStyle(max_grazing_angle: float | None = None)` in
   **degrees**.  `None`/`<= 0` disables the filter; `0 <= angle < 90` is
   validated (`ValueError` for `>= 90`).  Serialized uniform
   `u_max_stretch = tan(radians(angle))`, with `0.0` meaning off.
2. **Vertex measure** — `varying float vStretch` is the maximum over the four
   neighbour pairs (±u, ±v) of the **apparent slope** (tan of the grazing
   angle):
   - Pinhole: `slope_u = |zN − zC| · u_fx · uDepthSize.x / (zC · u_frame_size.x)`
     and `slope_v = |zN − zC| · u_fy · uDepthSize.y / (zC · u_frame_size.y)`,
     with `zC` guarded by `max(zC, 1e-6)`.
   - Orthographic: `slope_u = |zN − zC| · |u_depth_scale| / uWorldStep.x` and
     `slope_v = |zN − zC| · |u_depth_scale| / uWorldStep.y`, with the step
     guarded by `max(…, 1e-6)`.
   - A missing centre **or** missing neighbour contributes `0` for that pair
     (missing vertices are already handled by `vValid`).
3. **Fragment discard** — placed between the `u_discard_missing` and segment
   discards: `if (u_max_stretch > 0.0 && vStretch > u_max_stretch) discard;`.
4. **Renderer** — `u_max_stretch: { value: u.u_max_stretch ?? 0.0 }` in
   `buildDepthUniforms`.  No special-case in `applyDepthImageUniforms` (float).
5. **No new convenience helper** — the user keeps the returned `VizObjectRef`
   and calls `ref.set_uniform("u_max_stretch", …)` directly.  No
   `VizObjectRef.set_max_grazing_angle`, no new `Scene` method.

## Decisions (confirmed)

- **Angle-only API** (`max_grazing_angle` in degrees); no unitless `max_stretch`
  field (the issue offers either; the acceptance test only uses the angle).
- **Slope measure** (`tan(grazing angle)`) instead of the `1 − |dot(ray, n)|`
  form — equivalent, maps 1:1 to the angle, and is per-neighbour-pair without
  building four triangle normals.
- **No `VizObjectRef` helper** (confirmed with user) — runtime changes go
  through `ref.set_uniform("u_max_stretch", …)`.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-python-model-serialization.md](./01-python-model-serialization.md) | `DepthImageStyle.max_grazing_angle` + `u_max_stretch` serialization + tests |
| 2 | [02-frontend-shaders-uniform.md](./02-frontend-shaders-uniform.md) | Vertex `vStretch` + fragment discard + renderer uniform + JS tests |
| 3 | [03-cpu-reference-test.md](./03-cpu-reference-test.md) | CPU reference test: box/plane + tilted plane |
| 4 | [04-example-pinhole-slider.md](./04-example-pinhole-slider.md) | `pinhole_depth.py` box-in-plane + grazing-angle slider |
| 5 | [05-docs-changelog.md](./05-docs-changelog.md) | User docs + changelog |

## Testing as you go

- `uv run pytest py/tests/viz/test_depth_image.py py/tests/viz/test_depth_image_stretch.py -q` — Python regression + reference test.
- `uv run ruff check .` / `uv run ty check` — lint + type gates.
- `node js/dev/tests/check-syntax.mjs` — frontend syntax gate.
- `node --test js/dev/tests/depth-shader.test.mjs` — JS shader unit tests.
- `uv run python tools/build-viewer-js.py --check` — bundle drift gate (after template edits).
- `uv run python tools/generate-example-docs.py --check` — example docstring gate (phase 4).
- `uv run mkdocs build --strict` — docs gate (phase 5).

## Non-goals

- No `VizObjectRef`/`Scene` convenience method for the angle.
- No change to missing-depth (`vValid`/`u_discard_missing`) or segmentation
  (`tangaSegmentSelected`) semantics.
- No application-side band dilation (the `calib-auto-labelling` ground-plane /
  point-cloud depth borders are handled there, per the issue).
- No lens-distortion support.
