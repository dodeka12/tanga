# Image Canvas

`ImageCanvas` displays a numpy image in a dedicated 2D scene with a **y-down
pixel frame** (1 unit = 1 pixel), and lets you draw overlays in pixel
coordinates, swap in custom GLSL shaders, and bind mouse drag/click
interaction.

## Topics

| Guide | What you will learn |
|-------|---------------------|
| [Image Canvas](image-canvas.md) | `ImageCanvas`/`ImageData`, the pixel frame, overlays, `scene_view()` |
| [Custom Shaders](custom-shaders.md) | `register_shader`/`register_uniform`/`set_uniform`, the GLSL contract |
| [Interaction](interaction.md) | `DragBinding`/`ClickBinding`, drag/click handlers, cursors, `ActRectangle2D` |
| [Image transport](image-transport.md) | `codec`/`jpeg_quality`, JPEG vs lossless zlib, when to use which |
| [Tiled images](tiled-images.md) | `register_image_pyramid`, tile pyramids for very large images |
| [Image streams](image-stream.md) | `register_camera_stream`, 15–30 Hz MJPEG camera feeds |

## Runnable examples

- `py/examples/viz/image/image_canvas.py` — gradient with a rectangle overlay and
  a ctrl+drag brightness/contrast handler.
- `py/examples/viz/image/custom_shader_rgb_rotate.py` — a custom fragment shader
  that rotates each pixel's RGB vector, driven by a drag uniform.
- `py/examples/viz/image/rectangle_labeling.py` — a toolbar button arms a
  drag-to-draw rectangle mode (`ActRectangle2D`).
- `py/examples/viz/image/standard_image.py` — an 8-bit image over the default
  (JPEG) transport.
- `py/examples/viz/image/raw_image.py` — a 16-bit image over the lossless
  (zlib) transport.
- `py/examples/viz/image/huge_image.py` — a programmatic noise image served as
  a tile pyramid.
- `py/examples/viz/camera/camera_stream.py` — a 30 Hz MJPEG camera feed.
