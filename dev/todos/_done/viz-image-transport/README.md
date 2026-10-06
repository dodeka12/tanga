# Image Transport — Overview

**Created:** 2026-09-24 | **Status:** Done | **Branch:** `feat/image-transport`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Replace the current raw-bytes image pipeline (`_image_wire.py` →
`Transport.send_bytes` → `image-frames.js` → `makeDataTexture`) with a
three-tier transport, all still driven by the existing `ImageData` /
`ImageView` / `CameraView.background_image` API:

1. **In-band compressed frames** (JPEG for 8-bit, zlib for 16-bit/float) for
   small/medium images and interactive cameras over the existing WebSocket
   binary channel.
2. **HTTP tile pyramid** (`/image/{id}/{level}/{x}/{y}`) for very large single
   images (360° HDR, panoramas, whole-slide) — region-of-interest + resolution
   on demand, multi-consumer by pull + server cache.
3. **MJPEG-over-HTTP stream** (`/stream/{id}`) for 15–30 Hz camera feeds.

Additionally, **package eligible images as JPEG by default in exported HTML**
(instead of raw base64), with a lossless fallback for non-8-bit data.

## Architecture (short)

- **Wire format v2** — the binary image frame gains a `codec` byte (see the
  fixed contract below).  Python encodes; the frontend decodes.  Version bumps
  from 1 to 2 so old/new frames never silently mismatch.
- **Tile + stream routes** — two new aiohttp routes registered in
  `VizServer._build_app` (more specific than the existing `/{name:.*}`
  catch-all).  Tiles are a pull model (per-browser requests, server-side LRU
  cache); the MJPEG stream is a multipart push model.
- **Export asset store** — `AnimationRecording._image_asset` becomes the single
  choke point that emits JPEG data URLs for eligible images and raw base64 for
  the rest.
- **Frontend** — `image-frames.js` parses `codec`; `renderers/image.js` and
  `renderers/image-background.js` decode compressed frames via
  `createImageBitmap` (off-main-thread) and keep the existing raw
  `DataTexture` path for lossless/float data.

## Decisions (confirmed)

- Three-tier pipeline (in-band codec / tile pyramid / MJPEG), as approved.
- **Codec auto-selection** (`codec="auto"`, the default): `uint8` with 1 or 3
  channels → JPEG (quality 85); everything else (`uint16`, `float32`, 4-channel)
  → zlib-raw (lossless).  `codec="raw"` preserves today's exact behaviour;
  `codec="jpeg"`/`codec="zlib"` force a codec.  `ImageData` gains optional
  `codec` and `jpeg_quality` fields (both default `None` = auto).
- **Pillow is an optional runtime extra** (`pip install tanga-py[images]`),
  imported lazily (mirrors the existing `pil_to_numpy`); `zlib` is stdlib and
  used for the lossless path so no Pillow is required for float/16-bit data.
- **JPEG-by-default export** — eligible images (`uint8`, 1 or 3 channels) are
  embedded as `data:image/jpeg;base64,…` data URLs (source `url`), reusing the
  frontend's existing `url` texture path; ineligible images keep raw base64
  (source `data`).  Default JPEG quality 85.
- **Tile/stream semantics are IIIF-inspired, not full IIIF** — minimal,
  purpose-built endpoints (see contracts), no full IIIF/JPIP/WebRTC/HLS
  compliance.
- **Branch:** `feat/image-transport` (proposed — adjust if you want it folded
  into a different branch).

## Fixed wire contract (v2)

Binary frame layout (little-endian); offsets are absolute bytes into the frame:

| Offset | Size | Field |
|-------:|-----:|-------|
| 0 | 4 | magic `"TGI\0"` |
| 4 | 1 | `version` u8 = **2** |
| 5 | 1 | `type` u8 = 1 (image) |
| 6 | 1 | `id_len` u8 |
| 7 | 1 | `codec` u8 — 0=raw, 1=jpeg, 2=zlib-raw |
| 8 | 4 | `width` u32 |
| 12 | 4 | `height` u32 |
| 16 | 1 | `channels` u8 |
| 17 | 1 | `dtype` u8 — 0=uint8, 1=uint16, 2=float32 |
| 18 | 8 | `data_len` u64 (payload length after id bytes) |
| 26 | `id_len` | `id` ASCII bytes |
| 26+`id_len` | `data_len` | payload (raw pixels \| JPEG bytes \| zlib(raw pixels)) |

Python `struct` format: `"<BBBBIIBBQ"` (22 header bytes after magic).

`decode_image_frame` must accept **both** v1 (codec implied 0) and v2, so a
stale cached frontend never crashes on v1 frames; `encode_image_frame` always
emits v2.

## Tile URL contract

```
GET /image/{image_id}/{level}/{x}/{y}?format=jpeg|png|raw&quality=85
```

- `level 0` = full resolution; each level halves dimensions; tiles are
  `tile_size` (default 256) square, edge tiles clipped.
- Response `Content-Type`: `image/jpeg` (uint8 display), `image/png` (lossless
  16-bit), or `application/octet-stream` (raw/zlib float32).
- Backend holds the source array once and builds the pyramid lazily; an
  in-memory LRU caches encoded tiles so many consumers sharing a view are cheap.
- 404 for out-of-range `{level}/{x}/{y}`; 400 for an unknown image id.

## Stream URL contract

```
GET /stream/{stream_id}   → multipart/x-mixed-replace; boundary="tanga"
```

- Each part: `Content-Type: image/jpeg` + one JPEG frame.
- `CameraStream`/`ImageStream` Python object with `.publish(image)`; the server
  encodes once and fans the latest frame out to subscribers (v1: no per-client
  resolution negotiation — that is the tile pyramid's job).

## Examples (one per use-case)

Authored in Phase 7, each with a module docstring + `Keywords:` header (see
`dev/workflows/example-docs.md`).  The **huge image** and **image stream**
examples are generated from programmatic noise.

| Use-case | Script | Notes |
|----------|--------|-------|
| standard image | `py/examples/viz/image/standard_image.py` | uint8 RGB synthetic pattern, default (JPEG) in-band codec |
| raw image | `py/examples/viz/image/raw_image.py` | uint16 gradient, lossless zlib path, value-range uniforms |
| huge image | `py/examples/viz/image/huge_image.py` | programmatic noise → `register_image_pyramid` → tiled pane |
| image stream | `py/examples/viz/camera/camera_stream.py` | programmatic noise at 30 Hz → `register_camera_stream` |

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-image-codec-wire.md](./01-image-codec-wire.md) | Python codec layer + wire v2 + optional Pillow extra |
| 2 | [02-frontend-codec-decode.md](./02-frontend-codec-decode.md) | Frontend codec decode (createImageBitmap / zlib) |
| 3 | [03-export-jpeg-default.md](./03-export-jpeg-default.md) | JPEG-by-default in exported HTML asset store |
| 4 | [04-image-pyramid-server.md](./04-image-pyramid-server.md) | ImagePyramid + `/image/{id}/{level}/{x}/{y}` route + LRU |
| 5 | [05-tiled-imageview-frontend.md](./05-tiled-imageview-frontend.md) | Frontend tiled ImageView/background (viewport-driven tiles) |
| 6 | [06-mjpeg-camera-stream.md](./06-mjpeg-camera-stream.md) | CameraStream + `/stream/{id}` MJPEG + frontend |
| 7 | [07-examples.md](./07-examples.md) | Four example scripts (standard / raw / huge / stream) |
| 8 | [08-docs-changelog.md](./08-docs-changelog.md) | Developer docs, user docs, example docs, changelog |

## Testing as you go

```powershell
uv run pytest py/tests/viz -q          # fast viz gate
uv run pytest -q                       # full suite
uv run ruff check .                    # lint + ANN
uv run ty check                        # type correctness
node --test 'js/dev/tests/*.test.mjs'  # JS unit tests
node js/dev/tests/check-syntax.mjs     # JS syntax gate
uv run mkdocs build --strict           # docs
```

## Non-goals

- WebRTC / HLS / MPEG-DASH / JPIP / full IIIF compliance (kept as future work).
- JPEG-XL / AVIF (no broad browser support needed for a research tool).
- Fixing the pre-existing gap where **static** (non-animated) HTML snapshot
  export does not embed image pixel bytes (only the animated export's asset
  store does) — surfaced here, but out of scope unless the user confirms.
- Per-client resolution negotiation on the MJPEG stream (defer to the tile
  pyramid).
