# Custom Shaders

`ImageCanvas` renders its image with a GLSL fragment shader.  The standard shader
just samples the image texture; you can replace it with a custom one and drive it
with named uniforms set from the backend.

Floating-point HDR images (`read_exr`/`read_hdr`) often hold values above `1.0`,
which the default normalisation clamps — see [HDR images](hdr-images.md) for
setting `u_value_max` or swapping in a tone-mapping shader.

## Registering a shader

```python
canvas.register_shader(fragment_source, vertex=None)
```

`fragment` is the GLSL fragment shader source (a `str`).  `vertex` is an optional
custom vertex shader; omit it to keep the standard one.

## Registering and setting uniforms

```python
canvas.register_uniform("u_angle", 0.0)    # register a default (keeps existing value)
canvas.set_uniform("u_angle", 1.57)        # set + push a live update
```

- `register_uniform(name, default)` registers a uniform with a default, **keeping
  an existing value** (`setdefault` semantics).
- `set_uniform(name, value)` sets a uniform and pushes an `image_update` to the
  browser immediately — no image bytes are re-sent.

Uniform values are `float` or `int`.

## The shader contract

The renderer always provides:

| Name | Type | Meaning |
|------|------|---------|
| `vUv` | `vec2` (varying) | UV coordinate of the current pixel |
| `uImage0` | `sampler2D` | The primary image texture (mipmapped) |
| `uImageSize` | `vec2` | Level-0 image size in pixels (`width, height`) |

Any uniform you `register_uniform`/`set_uniform` is available by name in the
shader.  `uImage1` … `uImage3` are bound for the additional image layers.

## Minification & filtering

The image textures are **mipmapped** and use **linear minification** with
**nearest magnification**, so the standard shader renders hard 1:1 pixels when
zoomed in and smooth, flicker-free downscaling when the whole image is zoomed
out.

- A custom shader that samples the texture directly — `texture2D(uImage0, vUv)`
  — inherits this filtering for free: the GPU picks the right mip level from the
  pixel derivatives.
- A custom shader that does its own nearest-neighbour tap
  (`(floor(vUv * uImageSize) + 0.5) / uImageSize`) samples **level 0 only**, so
  it **opts out** of minification filtering — crisp at 1:1, but it may alias
  when the image is shown smaller than its native size.
  - To force an exact level-0 tap while keeping the texture available to other
    code, use `textureLod(uImage0, uv, 0.0)`.

`uImageSize` is always the **level-0 (full-resolution)** pixel size, regardless
of filtering.

## Example — RGB rotation around the grayscale axis

`py/examples/viz/image/custom_shader_rgb_rotate.py` replaces the standard shader
with one that rotates each pixel's RGB vector around the grayscale axis
`(1,1,1)/√3`, driven by a `u_angle` uniform bound to a left-drag handler:

```glsl
precision highp float;
varying vec2 vUv;
uniform sampler2D uImage0;
uniform vec2 uImageSize;
uniform float u_angle;

void main() {
    // Level-0 nearest-neighbour tap (opts out of minification filtering).
    vec2 snap = (floor(vUv * uImageSize) + 0.5) / uImageSize;
    vec3 rgb = texture2D(uImage0, snap).rgb;

    // Rotate the RGB vector around the grayscale axis (1,1,1)/sqrt(3).
    vec3 axis = normalize(vec3(1.0));
    float c = cos(u_angle);
    float s = sin(u_angle);
    vec3 rotated = rgb * c
        + cross(axis, rgb) * s
        + axis * dot(axis, rgb) * (1.0 - c);

    gl_FragColor = vec4(clamp(rotated, 0.0, 1.0), 1.0);
}
```

```python
canvas.register_shader(_FRAGMENT)
canvas.register_uniform("u_angle", 0.0)
```

Because `set_uniform` sends only a JSON `image_update`, dragging updates the
angle live without re-uploading pixels — see [Interaction](interaction.md) for
binding the drag handler.
