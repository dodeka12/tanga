# Viz Image Canvas — Overview

**Created:** 2026-09-13 | **Status:** In progress | **Branch:** `feat/image-view`

## Goal

Display raster images (numpy arrays, and optionally PIL images) inside the Tanga
viewer on a three.js plane drawn by a **fragment shader**, with a **pixel-based
coordinate frame** (origin top-left, x right, y down; 1 unit = 1 pixel) so
overlays can be drawn on the image in pixel coordinates and the mouse reports
pixel positions.  A user-facing `ImageCanvas` helper (analogous to
`CoordinateSystem`) owns a **dedicated 2D scene**, an interactive image plane
(`ActImagePlane`), an overlay draw group, and the machinery to register custom
fragment shaders, per-shader uniforms, and bind them to mouse handlers.

## Architecture (short)

- **Two backend objects**: `ImageView` (low-level: the active draw plane + N≤4
  textures + shader/uniform state, serialized to a new `image` entity kind) and
  `ImageCanvas` (user-facing helper like `CoordinateSystem`, owning the scene,
  the `ActImagePlane`, the overlay group, and the default handlers).  A frontend
  `image.js` renderer mirrors `ImageView`.
- **Dedicated 2D scene per canvas** with a **y-down pixel frame** (world unit =
  1 pixel) so `world_position` from interaction *is* the pixel position.
- **Images travel as raw binary WebSocket frames** (a length-prefixed envelope);
  uniforms and overlays travel as JSON and **never re-transmit the image**.
- **Export asset store**: images are stored once (keyed by id) outside the
  per-frame entity snapshots; an optional `url` source loads at runtime instead
  of embedding base64.

## Canonical wire contract (fixed up front; both sides implement against this)

### Image data model

- dtypes: `uint8` (code 0), `uint16` (code 1), `float32` (code 2).
- channels: 1, 3, or 4; memory layout C-contiguous H×W×C.
- Channel modes (`u_mode`): `0` = grayscale (channel 1), `1` = RGB (channels
  1–3), `2` = magnitude √(R²+G²+B²) of channels 1–3, `3` = channel 4 as
  grayscale.  Default: `1` for 3/4 channels, `0` for 1 channel.

### Binary image frame (server → client)

Little-endian, fixed header + raw C-contiguous bytes:

```
magic    4 bytes  "TGI\0"
version  1 byte   1
type     1 byte   1 (image)
id_len   1 byte   N
id       N bytes  ASCII image id
width    4 bytes  uint32
height   4 bytes  uint32
channels 1 byte
dtype    1 byte   (0=uint8, 1=uint16, 2=float32)
data_len 8 bytes  uint64
data     data_len bytes
```

Client sets `ws.binaryType = 'arraybuffer'` and branches on `event.data`
`instanceof ArrayBuffer` before JSON parsing.

### Image entity (JSON, in the scene object list)

```json
{
  "id": "img1",
  "layer": "scene",
  "kind": "image",
  "frame": { "width": 800, "height": 600 },
  "images": [
    { "id": "img1", "width": 800, "height": 600, "channels": 3, "dtype": 0,
      "source": "data" }
  ],
  "shader": { "fragment": "<glsl>", "vertex": "<glsl-or-null>" },
  "uniforms": {
    "u_mode": 1, "u_value_min": 0.0, "u_value_max": 1.0,
    "u_brightness": 0.0, "u_contrast": 1.0, "u_midpoint": 0.5
  }
}
```

`shader.fragment` defaults to the standard shader (brightness/contrast/mid +
channel modes).  A `source:"url"` image replaces the binary frame with
`"url": "…"` and the client loads it via `THREE.TextureLoader`.

### Uniform update (server → client, JSON)

```json
{ "type": "image_update", "scene": "<name>", "id": "img1",
  "uniforms": { "u_brightness": 0.25 } }
```

No image re-transmission.

### Standard shader contract

Applied to the normalized [0,1] value after channel selection:

```
out = clamp((in − mid) * contrast + mid + brightness, 0.0, 1.0)
```

Uniforms: `u_brightness` ∈ [−1,1] (default 0), `u_contrast` ∈ [0,∞) (default
1), `u_midpoint` ∈ [0,1] (default 0.5).  `u_value_min`/`u_value_max` normalize
the raw float to [0,1] first.  A custom shader may ignore all standard uniforms.

### Export asset store

```
assets: { "<image_id>": { "kind": "image", "source": "data"|"url",
  "data": "<base64>" | "url": "…", "width", "height", "channels", "dtype" } }
```

Entity snapshots reference image ids; assets are stored once.
`AnimationRecording.capture_frame(include_images=False)` re-registers assets
only when `include_images=True`.

## Decisions (confirmed)

- `ImageCanvas` (backend helper) + `ImageView` (plane+texture+shader) naming.
- Dedicated 2D scene with y-down pixel frame; `(0,0)` = top-left pixel center,
  `(0.5,0.5)` = its bottom-right corner.
- Mouse binds to a backend handler → `set_uniform` → JSON update over the same WS.
- `ActImagePlane` reuses `ActSceneObject` + `drag_anchor` = ray↔plane hit.
- Fixed 4 image layers; allocation failure reported via the existing log pipeline.
- Nearest-neighbour zoom; rotation AA via a derivative/axis-aligned gate in the
  fragment shader.
- dtypes `uint8`/`uint16`/`float32`; `pil_to_numpy(img, *, dtype="uint8")` with
  lazy PIL import; Pillow added to the dev dependency group (not a runtime extra).
- Overlay = a `VizGroup` in the pixel frame; any drawable entity.
- Raw binary WS frames for image data; JSON for uniforms/overlays.
- Export asset store + optional URL + `capture_frame(include_images=False)`.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-python-image-data-model.md](./01-python-image-data-model.md) | `ImageData` + dtype/channel model, normalization, `pil_to_numpy`, Pillow dev dep |
| 2 | [02-imageview-backend.md](./02-imageview-backend.md) | `ImageView` (planes/textures/shader/uniform state) + serialization |
| 3 | [03-act-image-plane.md](./03-act-image-plane.md) | `ActImagePlane` interactive object + `drag_anchor` |
| 4 | [04-imagecanvas-backend.md](./04-imagecanvas-backend.md) | `ImageCanvas` helper: scene, overlay group, API, wiring |
| 5 | [05-binary-transport.md](./05-binary-transport.md) | Binary WS frame encode/decode + transport plumbing |
| 6 | [06-frontend-image-renderer.md](./06-frontend-image-renderer.md) | `renderers/image.js` ShaderMaterial + textures + nearest/AA gate |
| 7 | [07-server-integration.md](./07-server-integration.md) | Route `image` entity + `image_update` + binary send, `Visualizer` glue |
| 8 | [08-interaction-wiring.md](./08-interaction-wiring.md) | Plane raycast → pixel coords → backend handler → uniform |
| 9 | [09-export-asset-store.md](./09-export-asset-store.md) | Export asset store + URL source + recording flag |
| 10 | [10-example.md](./10-example.md) | End-to-end example(s) |
| 11 | [11-docs-changelog.md](./11-docs-changelog.md) | Architecture docs + public docs + changelog |

## Testing as you go

- **Python:** `uv run pytest py/tests/viz -q` (targeted files per phase).
- **JS (pure modules):** `node --check <file>` for syntax; the shader math
  (dtype/normalization/AA gate) is a pure `image-shader.js` module tested with
  Node's built-in runner (`node --test 'dev/src/js-tests/*.test.mjs'`) where DOM
  is not needed.
- **Browser/WebGL** (`image.js`, `interaction.js`, `viewer.js`): browser smoke
  pages + the existing manual viewer.
- **Docs:** `uv run mkdocs build --strict`.
- Every phase ends with a runnable validation command before the next phase
  starts — no "test phase at the end".

## Non-goals

- No change to `CoordinateSystem` / 2D camera stretch semantics.
- PIL is a dev/test-only dependency, not a runtime extra (lazy import).
- 3D-object texturing is out of scope, but the export asset store is shaped to
  accommodate it later (id-keyed, not image-specific).
- No new `DragMode`: the image plane reuses `XY_PLANE` (its own plane) in 2D.

## Guiding decisions / no-refactor rule

- The wire contract above is **fixed now**; later phases implement *against* it.
- `ImageView` serialization precedes the frontend renderer; `ActImagePlane`
  precedes interaction wiring; the binary transport precedes server integration.
- Image pixel data is sent exactly once per `set_image`; uniforms/overlays are
  JSON-only updates.

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this work
touches, so the new code aligns with the documented architecture. If this work
introduces or changes architecture, update the developer docs.
