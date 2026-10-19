# Depth Images (2.5D surfaces)

A **depth image** renders a per-pixel depth map as a **2.5D heightfield surface**
in the normal 3D viewer.  A vertex shader builds the grid from the depth texture,
computes a surface normal by finite differences, and sets the UVs; a fragment
shader colors it with a depth colormap (default), the texture-mapped source
image, or a **plain color shaded by the per-scene lighting** (ambient +
directional + Blinn-Phong specular) — or a custom shader.  An optional
segmentation mask can hide non-selected segments.  The mesh places one vertex at
each depth **pixel center** and interpolates smoothly between them, so the
surface follows the depth map rather than appearing as flat quads.

```python
import numpy as np
from pytanga.viz import DepthImage, DepthImageData, DepthImageStyle, Visualizer

data = DepthImageData(
    image=np_img,          # H×W×3 uint8 (optional)
    depth=np_depth,        # H×W float32 (required; may differ in size from image)
    segmentation=np_seg,   # H×W uint8/uint16 integer labels (optional)
)

depth = DepthImage(data, selected_segments=[1, 2, 3])

viz = Visualizer(add_default_grid=False)
ref = viz.new(
    depth,
    style=DepthImageStyle(
        render_mode="depth",  # "depth" (default) | "image" | "plain"
        colormap="turbo",     # "viridis" | "turbo" | "gray"
        mesh_scale=0.5,       # mesh + transmitted depth resolution fraction
        world_scale=0.01,     # world units per reference pixel
        depth_scale=2.0,      # world units per depth unit (negative inverts)
    ),
)
viz.show()
viz.wait()
```

## Data model

`DepthImageData` bundles the three numpy arrays.  Only `depth` is required, and
the arrays may have **different pixel resolutions** — they are all sampled by
normalized UV (0..1) across the same extent, so the borders fit.  Non-finite
depth values (NaN/±inf) are replaced with a `missing_depth` sentinel (default
`-3.402823466e38`).

`DepthImage` is the entity: it wraps the data plus a custom shader and uniforms
(the standard shader "handler" pattern) and the initial segment selection.

## `DepthImageStyle`

| Field | Type | Default | Meaning |
|-------|------|---------|---------|
| `render_mode` | `str` | `"depth"` | `"depth"` (colormap), `"image"`, or `"plain"` (lit by scene lighting) |
| `colormap` | `str` | `"turbo"` | `"viridis"`, `"turbo"`, or `"gray"` |
| `mesh_scale` | `float` | `1.0` | Fraction of the **depth** resolution used for the mesh (0..1) |
| `max_mesh_size` | `int` | `512` | Cap on the longest grid side (cells) |
| `image_scale` | `float` | `None` | Transmitted image resolution fraction (`None` = full) |
| `segmentation_scale` | `float` | `None` | Transmitted segmentation fraction (`None` = follow image) |
| `camera` | `CameraCalibration`/`PinholeCamera` | `None` | Pinhole intrinsics (from `K` or `fx`/`fy`/`cx`/`cy`) + optional pose |
| `depth_kind` | `str` | `"axial"` | `"axial"` (depth along optical axis), `"radial"` (distance along ray), or `"inverse"` (inverse depth `1/Z`) |
| `apply_pose` | `bool` | `True` | Auto-apply a `CameraCalibration`'s `camera_to_world()` pose |
| `codec` | `EImageCodec` | `None` | `RAW`/`JPEG`/`ZLIB`; `None` auto-selects per frame |
| `jpeg_quality` | `int` | `None` | JPEG quality when JPEG is used |
| `world_scale` | `float` | `1.0` | World units per reference pixel |
| `depth_scale` | `float` | `1.0` | World units per depth unit (negative inverts) |
| `depth_offset` | `float` | `0.0` | Depth subtracted before scaling |
| `depth_min` / `depth_max` | `float` | `0.0`/`1.0` | Colormap/clamp range (axial metres in pinhole mode; raw depth units in orthographic mode) |
| `discard_missing` | `bool` | `True` | Discard missing-depth fragments |
| `double_sided` | `bool` | `True` | Render both sides |
| `color` / `opacity` | `str`/`float` | `#ffffff`/`1.0` | Plain-mode color / surface opacity |
| `shininess` | `float` | `32.0` | Blinn-Phong specular exponent (plain mode) |
| `specular` | `str` | `#ffffff` | Blinn-Phong specular color (plain mode) |

## Downscaling & compression

The arrays are **downscaled Python-side before encoding**, so only the needed
resolution is transmitted: `depth` to the mesh resolution (`mesh_scale`, applied
to the *depth* resolution), `image` to `image_scale`, `segmentation` to
`segmentation_scale`.  Depth and segmentation use nearest-neighbour (preserving
the sentinel and integer labels); the color image uses area/bilinear.  `codec`
reuses `EImageCodec`: `None` auto-selects (JPEG for a uint8 1/3-channel color
image, ZLIB otherwise); an explicit `JPEG` applies only to the color image —
depth/segmentation are always
lossless.

## Pinhole camera mode

For a calibrated depth map, `DepthImageStyle(camera=…)` switches the surface from
an orthographic heightfield to a **pinhole** surface whose vertices live in the
camera frame (x right, y down, z forward, as in `CameraCalibration`):

```python
from pytanga.geometry import Matrix, OpenCVFrame
from pytanga.viz import CameraCalibration, DepthImage, DepthImageData, DepthImageStyle

calib = CameraCalibration(K=..., R=..., t=..., image_size=(w, h),
                          frame=OpenCVFrame(), units=1.0)

viz.new(
    DepthImage(DepthImageData(depth=np_depth)),
    style=DepthImageStyle(camera=calib, depth_kind="z"),
)
```

- Intrinsics come from `K` (a `CameraCalibration`) or `fx`/`fy`/`cx`/`cy` (a
  `PinholeCamera`), in pixels of the **full-resolution reference frame**
  (`DepthImageData.frame`, the image if present else the depth), so a downscaled
  mesh/depth still uses the original intrinsics.
- `depth_kind` selects the raw-depth interpretation — `"axial"` (depth along the
  optical axis, `Z = (depth − depth_offset) · depth_scale`), `"radial"`
  (Euclidean distance along the ray), or `"inverse"` (inverse depth `1/Z`, e.g.
  disparity).  Aliases `"z"`, `"range"`, `"disparity"` are accepted.  Vertex
  `X = (u−cx)/fx·Z`, `Y = (v−cy)/fy·Z`.
- `depth_scale`/`depth_offset` stay as the unit conversion; `world_scale` is
  ignored in this mode.
- `depth_min`/`depth_max` are always expressed in **axial metres** (world units
  of `Z`), regardless of `depth_kind` — the raw value is converted to `Z` first,
  then clamped for the colormap and surface extent.
- `apply_pose=True` (default) applies a `CameraCalibration`'s
  `camera_to_world()` so the surface lands at its true world pose.  The surface
  is always placed **relative to the camera** — the intrinsics give the ray
  through each pixel, the depth gives the distance along it, and the calibration
  pose (whatever its rotation and translation) places the result in the world —
  so it moves correctly with arbitrary extrinsics.  Set `apply_pose=False` to
  leave it in the camera frame and place it with the entity `transform`.
  Normals, segmentation selection, and the plain/image/depth render modes keep
  working.

## Segmentation filtering

Set `DepthImage(..., selected_segments=[...])` initially, then switch the
selection live — a granular uniform update, no pixel re-send, no mesh rebuild:

```python
ref.set_selected_segments([1, 2])   # show only these ids
ref.set_selected_segments([])       # disable filtering (show all)
```

Filtering is a fragment `discard` on non-selected ids, so hidden segments write
neither color nor depth.

## Live uniforms and custom shaders

```python
ref.set_uniform("u_angle", 1.57)    # any custom uniform, pushed live
```

`DepthImage(data, fragment=..., vertex=..., uniforms={"u_angle": 0.0})` registers
a custom shader.  The renderer always provides:

| Name | Type | Meaning |
|------|------|---------|
| `vUv` | `vec2` varying | Normalized surface UV |
| `vDepth` / `vValid` | `float` varyings | Clamped depth / missing-depth flag |
| `uDepth` | `sampler2D` | Depth texture (nearest, value in `.r`) |
| `uSegMask` | `sampler2D` | Segmentation texture (integer label in `.r`) |
| `uImage0` | `sampler2D` | Color image texture (mipmapped) |
| `uDepthSize` / `uSegSize` / `uImageSize` | `vec2` | Pixel sizes for nearest taps |
| `tangaSegmentSelected(vec2 uv)` | `bool` | Segment-membership helper (custom fragment shaders can call it) |

## Example

`py/examples/viz/image/depth_surface.py` builds a synthetic surface from
phase-shifted 2D sines, a higher-resolution color image, and a synthetic
segmentation mask; press `m` to cycle the render mode and `s` to cycle the
segment selection.

`py/examples/viz/image/pinhole_depth.py` places a calibrated camera at the world
origin and renders one constant depth map, with a control pane to switch
`depth_kind` (`axial`/`radial`/`inverse`) live — the same raw depth values then
produce a flat wall, a dome, or a nearer flat wall.
