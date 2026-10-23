# Phase 1 — Python data model + style

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/architecture/viz-architecture.md` ("New entity kind", "Image canvas
> (extension recipe)").  This phase adds the pure data model only; no scene/JS
> changes yet.

## Goal

Add `DepthImageData`, `DepthImage`, the `DepthImageMode`/`DepthColormap` enums,
and `DepthImageStyle`, with validation.  All pure data — no server/rendering
imports — so it is unit-testable in isolation (mirrors `image.py`).

## Files

- New: `py/pytanga/viz/depth_image.py`
- Edit: `py/pytanga/viz/_styles/_entity_styles.py` (add `DepthImageStyle`)
- Edit: `py/pytanga/viz/_styles/__init__.py` (import, `__all__`, `_DEFAULT_STYLE_FOR_KIND`)
- Edit: `py/pytanga/viz/__init__.py` (export)
- New: `py/tests/viz/test_depth_image.py`

## Steps

- [x] **1.1 — `depth_image.py` data model.**
  - Add `DepthImageMode` (`DEPTH=0, IMAGE=1, PLAIN=2`) and `DepthColormap`
    (`VIRIDIS=0, TURBO=1, GRAY=2`) `IntEnum`s, plus `MAX_SELECTED_SEGMENTS = 16`
    and `DEFAULT_MISSING_DEPTH = -3.402823466e38`.
  - Add `DepthImageData` (dataclass): `image: np.ndarray | None`,
    `depth: np.ndarray`, `segmentation: np.ndarray | None`.  Validate in
    `__post_init__`: `depth` required and 2-D; `image`/`segmentation` 2-D or
    3-D as appropriate; dtypes among uint8/uint16/float32; store C-contiguous
    copies.  Replace non-finite depth (NaN/±inf) with a `missing_depth` sentinel
    (param, default `DEFAULT_MISSING_DEPTH`).  Expose `frame` `(w, h)` =
    image shape if present else depth shape, and a `segmentation_ids()`
    convenience (sorted unique integer labels) where available.

- [x] **1.2 — `DepthImage` entity + downscaling.**
  - Dataclass wrapping a `DepthImageData` plus presentation fields:
    `fragment: str | None`, `vertex: str | None`, `uniforms: dict[str, int | float]`,
    `selected_segments: list[int] | None`.
  - Add `_downscale(arr, w, h, *, nearest) -> np.ndarray`: nearest-neighbour for
    depth/segmentation (preserves the missing sentinel and integer labels),
    area/bilinear for the color image.
  - Add `_serialize_uniforms(style) -> dict` mapping the resolved style +
    `selected_segments` into the `uniforms` block from the README contract
    (render mode, colormap, depth mapping, segmentation selection, color/opacity,
    then custom uniforms on top).
  - Add `_serialize_mesh(style, frame) -> dict` computing `segments_u/v` from
    `frame × mesh_scale` (capped so the long side ≤ `max_mesh_size`) plus
    `world_scale`.
  - Add `_build(style, entity_id) -> tuple[dict, list[ImageData]]` that
    downscales depth to the mesh resolution, image to `image_scale`,
    segmentation to `segmentation_scale`, wraps them as `ImageData` frames (ids
    `<eid>.depth` / `<eid>.seg` / image id, `tile_max_*` disabled, codec from
    `style.codec`), and returns `(payload, frames)` whose metadata
    `width`/`height` are the **downscaled** sizes.

- [x] **1.3 — `DepthImageStyle`.**
  - In `_entity_styles.py`, add `@dataclass DepthImageStyle(VizStyle)` with
    fields `render_mode`, `colormap`, `mesh_scale`, `max_mesh_size`,
    `image_scale`, `segmentation_scale`, `codec`, `jpeg_quality`, `world_scale`,
    `depth_scale`, `depth_offset`, `depth_min`, `depth_max`, `discard_missing`,
    `double_sided`, `color`, `opacity` (all `None`-defaulted); `to_dict()` dumps
    non-`None` fields with `style_type: "DepthImageStyle"`.  `codec` is an
    `EImageCodec | None`.  (`missing_depth` is *not* a style field — it lives on
    `DepthImageData`, the authoritative sentinel actually written into `depth`.)
  - Register it: import in `_styles/__init__.py`, add to `__all__`, and add
    `"DepthImage": DepthImageStyle(mesh_scale=1.0, max_mesh_size=512,
    image_scale=None, segmentation_scale=None, codec=None, jpeg_quality=None,
    world_scale=1.0, render_mode="depth", colormap="turbo", depth_scale=1.0,
    depth_offset=0.0, depth_min=0.0, depth_max=1.0, discard_missing=True,
    double_sided=True, color="#ffffff", opacity=1.0)` to
    `_DEFAULT_STYLE_FOR_KIND`.
  - Export `DepthImageStyle` from `py/pytanga/viz/__init__.py` (with the other
    styles) and add the new public names to its `__all__`.

- [x] **1.4 — Tests.**
  - `test_depth_image.py`: validation (missing depth raises; non-finite depth →
    sentinel; frame fallback to depth when image is `None`); `DepthImageMode` /
    `DepthColormap` codes; `DepthImage._build` against the README contract —
    including that the returned frame sizes match the downscaled
    `mesh_scale`/`image_scale`/`segmentation_scale` targets and that the
    `codec`/`jpeg_quality` reach the `ImageData` frames; `DepthImageStyle.to_dict()`
    and the canonical default merge.

## Validation

`uv run pytest py/tests/viz/test_depth_image.py py/tests/viz/test_viz_styles.py -q`

## Notes

- Keep `depth_image.py` free of `scene`/`transport`/`serializer` imports; it may
  import `numpy` and `image.py` (`ImageData`, `EImageCodec`) only.
- `render_mode`/`colormap` in the style are strings; convert to their enum codes
  inside `_serialize_uniforms`.
- `u_color` is stored as a `[r,g,b]` list in the payload; the JS renderer turns
  it into a `THREE.Vector3`.
- Downscaling is lossy-free only for nearest channels; never downscale
  segmentation with bilinear (would blend integer labels).
