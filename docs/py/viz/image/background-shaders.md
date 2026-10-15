# Background Image Shaders

A calibrated `CameraView.background_image` renders through a GLSL shader, just
like an `ImageCanvas`.  The default shader letterboxes/crops the image to the
calibrated projection and then applies the standard brightness/contrast (and
value-range) colour pipeline; you can replace the colour processing with a
custom fragment shader and drive it with named uniforms.

## Registering a shader

```python
viz.register_background_shader(view, fragment_source, vertex=None)
```

`fragment` is the GLSL fragment shader source (a `str`).  `vertex` is an optional
custom vertex shader; omit it to keep the standard one.  `view` is the
`SceneView` pane whose background is shaded.  Registering a shader re-pushes the
background so the frontend rebuilds the material with the new source.

## Registering and setting uniforms

```python
viz.register_background_uniform(view, "u_angle", 0.0)   # register a default (keeps existing value)
viz.set_background_uniform(view, "u_angle", 1.57)        # set + push a live update
```

- `register_background_uniform(view, name, default)` registers a uniform with a
  default, **keeping an existing value** (`setdefault` semantics).
- `set_background_uniform(view, name, value)` sets a uniform and pushes a
  `view_background_uniforms` message to the browser immediately — no image bytes
  are re-sent and no layout re-push happens.

Uniform values are `float` or `int`.

## The shader contract

The background renderer always provides:

| Name | Type | Meaning |
|------|------|---------|
| `vNdc` | `vec2` (varying) | NDC coordinate of the current pixel |
| `uImage` | `sampler2D` | The background image texture |
| `uImageAspect` | `float` | image width / height |
| `uPaneAspect` | `float` | pane width / height |
| `uFit` | `float` | `0.0` = letterbox (fit), `1.0` = stretch (fill) |
| `uCrop` | `vec4` | `(u0, v0, u1, v1)` normalized crop window |
| `uHx`/`uHy` | `float` | zoom-scaled letterbox half-extents (NDC) |

The standard colour uniforms (`u_value_min`/`u_value_max`, `u_brightness`,
`u_contrast`, `u_midpoint`, `u_mode`) and any uniform you register are also
available by name.  The default shader computes the letterbox/crop UV, samples
`uImage`, then applies `tangaSampleColor()` — the shared colour pipeline (channel
mode → value-range normalize → brightness/contrast → clamp) — before writing
`gl_FragColor`.

## Example — brightness/contrast via ctrl+drag

`py/examples/apps/calibrated_labeling_app.py` binds a
`DragBinding(MouseButton.LEFT, handler, ModifierKey.CTRL)` to the calibrated
surface; the handler maps horizontal drag to `u_contrast` and vertical drag to
`u_brightness` via `set_background_uniform`, exactly like the `ImageCanvas`
demos.
