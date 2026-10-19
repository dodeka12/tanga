# Depth image (2.5D surface) entity — Overview

**Created:** 2026-10-16 | **Status:** Done | **Branch:** `feat/depth-image`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-architecture.md` — the
> "New entity kind" and "Image canvas (extension recipe)" sections).  This work
> **adds a new scene entity kind** (`depth_image`) and a new granular message
> (`depth_image_update`), so the developer docs must be updated in Phase 7.

## Goal

Add a `depth_image` scene entity that renders a **2.5D heightfield surface** in
the normal 3D viewer.  The vertex shader builds the displaced grid and sets the
UVs; the fragment shader colors it with one of:

1. a **depth colormap** (default),
2. the **texture-mapped source image** (optional), or
3. a **plain color**,

or a developer-supplied **custom shader** via the standard shader/uniform
"handler" pattern.  An optional **segmentation mask** discards vertices that do
not belong to the selected segment ids (no color **and** no depth write),
switchable instantly through uniforms.

Image, depth, and segmentation are supplied as **numpy arrays**.  They may have
**different pixel resolutions** (only the extent must match — the borders fit):
all textures are sampled by normalized UV (0..1), each with its own resolution.

## Architecture (short)

Mirror the existing `image` entity end to end — it is already a payload-based
scene node with id-keyed binary pixel frames and a granular uniform message.

- **Python data model** (`py/pytanga/viz/depth_image.py`, new): `DepthImageData`
  (arrays) + `DepthImage` (entity) + `DepthImageMode`/`DepthColormap` enums.
  Pure data + validation, no server/rendering imports (mirrors `image.py`).
- **`DepthImageStyle`** in `_styles/_entity_styles.py` (mesh decimation,
  colormap, depth mapping, color/opacity), registered in `_DEFAULT_STYLE_FOR_KIND`.
- **`VizDepthImage`** (`_nodes.py`) — a payload node `kind == "depth_image"`,
  mirroring `VizImage`.  Pixels travel as the existing id-keyed binary frames
  (`_image_wire.py` → `image-frames.js`).
- **Frontend** — `renderers/depth-shader.js` (GLSL builders) + `renderers/depth-image.js`
  (mesh + textures), dispatched from `renderers/factory.js`; the granular
  `depth_image_update` message is handled in `templates/views/three-view.js`.

## Fixed contract (decided up front — later phases implement against this)

### Public API

```python
from pytanga.viz import (
    DepthImage, DepthImageData, DepthImageStyle,
    DepthImageMode, DepthColormap, EImageCodec, Visualizer,
)
import numpy as np

data = DepthImageData(
    image=np_img,          # H×W×3 uint8, optional
    depth=np_depth,        # H×W float32 (may differ in size from image)
    segmentation=np_seg,   # H×W uint8/uint16 integer labels, optional
)

depth = DepthImage(
    data,
    fragment="...", vertex="...",     # optional custom shader (handler pattern)
    uniforms={"u_angle": 0.0},        # optional custom uniforms
    selected_segments=[1, 2, 3],      # optional initial segment selection
)

ref = viz.new(  # or viz.add(...) -> str id
    depth,
    style=DepthImageStyle(
        render_mode="depth",     # "depth" (default) | "image" | "plain"
        colormap="turbo",
        mesh_scale=0.5,          # mesh + transmitted depth resolution fraction
        image_scale=0.25,        # transmitted image resolution fraction (None = full)
        segmentation_scale=0.5,  # transmitted segmentation fraction (None = follow image)
        codec=EImageCodec.ZLIB,  # None (auto) | RAW | JPEG | ZLIB
        jpeg_quality=85,
        world_scale=1.0,         # world units per reference pixel
        depth_scale=1.0, depth_offset=0.0,
        color="#4488ff", opacity=1.0,
    ),
)

ref.set_selected_segments([4, 5])   # live: pushes depth_image_update only
ref.set_uniform("u_angle", 1.57)    # live: pushes depth_image_update only
```

`DepthImageData` accepts `image`/`depth`/`segmentation` as numpy arrays; only
`depth` is required.  Non-finite depth values are replaced with `missing_depth`
(sentinel, default `-3.402823466e38`).  `DepthImageMode`: `DEPTH=0, IMAGE=1,
PLAIN=2`.  `DepthColormap`: `VIRIDIS=0, TURBO=1, GRAY=2`.

**Downscaling happens Python-side before encoding** (only the downscaled bytes
are transmitted): `depth` is transmitted at the mesh resolution (`mesh_scale`),
`image` at `image_scale`, `segmentation` at `segmentation_scale`.  Depth and
segmentation use nearest-neighbour downscaling (preserves the missing sentinel
and integer labels); the color image uses area/bilinear.  `codec` reuses
`EImageCodec` (`RAW`/`JPEG`/`ZLIB`); `None` auto-selects per frame (JPEG for a
uint8 1/3-channel color image, ZLIB otherwise).  An explicit `JPEG` applies only
to the color image — depth/segmentation always use a lossless codec.

### Wire entity dict (`kind == "depth_image"`)

```json
{
  "id": "<eid>", "layer": "scene", "kind": "depth_image",
  "parent_id": null,
  "transform": { "position": [0,0,0], "rotation": [0,0,0,1], "scale": [1,1,1] },
  "visible": true,
  "frame": { "width": 640, "height": 480 },
  "depth":       { "id": "<eid>.depth", "width": 320, "height": 240, "channels": 1, "dtype": 2, "source": "data" },
  "image":       { "id": "img", "width": 640, "height": 480, "channels": 3, "dtype": 0, "source": "data" },
  "segmentation": { "id": "<eid>.seg", "width": 640, "height": 480, "channels": 1, "dtype": 1, "source": "data" },
  "shader": { "fragment": null, "vertex": null },
  "mesh": { "segments_u": 64, "segments_v": 48, "world_scale": 1.0 },
  "uniforms": {
    "u_render_mode": 0, "u_colormap": 1,
    "u_depth_scale": 1.0, "u_depth_offset": 0.0,
    "u_depth_min": 0.0, "u_depth_max": 1.0,
    "u_missing_depth": -3.402823466e38, "u_discard_missing": 1,
    "u_seg_enabled": 0, "u_num_selected": 0,
    "u_selected_segments": [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    "u_color": [1,1,1], "u_opacity": 1.0
  }
}
```

- `frame` is the reference extent (image resolution if present, else depth);
  `world_scale` is world units per reference pixel.
- The `depth`/`image`/`segmentation` metadata `width`/`height` are the
  **transmitted (downscaled)** sizes, not the source resolutions.  Only these
  downscaled frames are sent.
- The surface is a `PlaneGeometry(frame.width * world_scale, frame.height *
  world_scale, segments_u, segments_v)` centred at the node origin (canonical XY
  plane, +Z normal); UVs are the plane's normalized 0..1.
- `mesh_scale`/`max_mesh_size` are resolved Python-side into `segments_u/v`
  (capped).  `u_selected_segments` has fixed length 16; `u_num_selected == 0`
  means "no filtering" (show all).
- `image`/`segmentation` are `null` when absent; the renderer binds a fallback
  (1×1) texture for those samplers.

### Granular uniform message

```json
{ "type": "depth_image_update", "scene": "<scene>", "id": "<eid>", "uniforms": { ... } }
```

Carries a partial uniform patch (e.g. `u_selected_segments`,
`u_num_selected`, `u_seg_enabled`, `u_render_mode`, `u_angle`, …).  No pixel
re-send, no mesh rebuild.

## Decisions (confirmed)

- **Mesh, not SDF.**  The spec requires a vertex shader that constructs the
  mesh and sets UVs; texture mapping, segmentation `discard`, picking, and
  custom vertex shaders are all trivial on a mesh, and a decimated grid
  (`mesh_scale`) keeps vertex counts bounded.  SDF is out of scope for v1.
- **`DepthImageData` + `DepthImage` split.**  Data (arrays) vs. presentation
  (entity), mirroring `ImageData` vs. `ImageView`, and extensible for future
  channels (normals, albedo, …).
- **Resolution decoupled.**  `depth`/`image`/`segmentation` may differ in size;
  only the extent matches; all are sampled by normalized UV.
- **Depth displaces along +Z** (canonical surface normal); `u_depth_scale` may
  be negative to invert.
- **Missing depth** (NaN/±inf) → sentinel `u_missing_depth`, clamped to
  `u_depth_min` and discarded by default (`u_discard_missing == 1`).
- **Segmentation filtering** is a fragment `discard` on non-selected ids (⇒ no
  color, no depth write); the selection is a uniform so it switches instantly.
- **Depth/segmentation textures use nearest filtering** at snapped pixel
  centres (no sentinel smearing, exact integer labels); the color image uses
  standard mipmapped filtering.
- **Transmit only the downscaled size.**  `mesh_scale`/`image_scale`/
  `segmentation_scale` are applied to the arrays Python-side (nearest for
  depth/seg, area/bilinear for image) before encoding, so the wire frames carry
  the mesh/texture resolution actually needed — never the full source
  resolution.
- **Compression reuses `EImageCodec`** via `DepthImageStyle.codec` (+
  `jpeg_quality`); auto per-frame otherwise, with depth/segmentation always
  lossless.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-python-data-model-and-style.md](./01-python-data-model-and-style.md) | `DepthImageData`, `DepthImage`, enums, `DepthImageStyle` |
| 2 | [02-scene-node-serialization-frames.md](./02-scene-node-serialization-frames.md) | `VizDepthImage` node + `Scene` serialization + binary frames |
| 3 | [03-viz-add-and-ref-uniform-api.md](./03-viz-add-and-ref-uniform-api.md) | `viz.add/new` routing + `VizObjectRef.set_uniform`/`set_selected_segments` |
| 4 | [04-frontend-shaders-and-renderer.md](./04-frontend-shaders-and-renderer.md) | `depth-shader.js` + `depth-image.js` + `factory.js` dispatch |
| 5 | [05-frontend-live-uniform-updates.md](./05-frontend-live-uniform-updates.md) | `depth_image_update` dispatch + `applyDepthImageUniforms` |
| 6 | [06-example-script.md](./06-example-script.md) | Example script (phase-shifted 2D sin surface) + smoke test |
| 7 | [07-docs-changelog.md](./07-docs-changelog.md) | Developer docs + user docs + changelog |

## Testing as you go

- `uv run pytest py/tests/viz -q` — Python regression (each phase adds its test file).
- `node js/dev/tests/check-syntax.mjs` — frontend syntax gate.
- `node --test js/dev/tests/*.test.mjs` — JS unit tests.
- `uv run python tools/build-viewer-js.py` — rebuild the committed viewer bundle after template edits.
- `uv run mkdocs build --strict` — docs gate (phase 7).
- Manual smoke: `uv run python py/examples/viz/image/depth_surface.py` (phase 6).

## Non-goals

- No SDF/ray-marched render path.
- No URL or tiled image sources for the depth entity (numpy arrays only in v1).
- No change to the binary image-frame wire format (`_image_wire.py`) or the
  `view_layout` shape.
- No `ImageCanvas`-style dedicated 2D canvas helper — this is an entity added to
  any scene, not a canvas.

