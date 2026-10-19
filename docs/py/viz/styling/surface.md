# Surface Textures & Shaders

Solid surface entities — `Plane`, `Sphere`, `Ellipsoid`, `Disk`, `Box`,
`Cylinder`, and `Cone` — can be textured by an image, a custom GLSL program, or
both.  Pass a `SurfaceMaterial` (or a bare `SurfaceShader` / `SurfaceTexture` /
sequence of textures, which are normalized automatically) via
`viz.add(..., surface=...)` or `viz.new(...)`, or set `surface=` on the per-kind
style (`SphereStyle`, `PlaneStyle`, …).

## Semantics

- No `surface` → the standard colored material.
- One or more textures, no shader → only the **first** texture is used, with the
  standard texture map (lit by the global scene lighting).
- A shader → replaces the standard shader.
- A shader + textures → the shader replaces the standard shader, and each
  texture is bound to its declared sampler `uniform`.
- Surface materials are opaque by default; they do not inherit the entity's
  translucent "shell" opacity.

## Standard texture map

```python
from pytanga.geometry import Point, Sphere
from pytanga.viz import ImageData, SurfaceMaterial, SurfaceTexture, Visualizer

tex = ImageData("tex0", data=...)   # a uint8 H×W×3 numpy array
viz.add(
    Sphere(Point(0.0, 0.0, 0.0), 1.0),
    surface=SurfaceMaterial(textures=[SurfaceTexture(image=tex)]),
)
```

## Custom shaders

`SurfaceShader` takes a GLSL fragment that defines
`vec3 surfaceColor(vec3 baseColor, vec3 n, vec3 p)` and returns the surface
color.  The host provides the varyings `vUv`, `vNormal`, `vWorldPosition`,
`vLocalPos`, the uniforms `u_color` / `u_opacity`, the global scene-lighting
uniforms (`uLightCount`, `uLightDir[]`, `uLightColor[]`, `uAmbientColor`), and a
`tangaLight(albedo, n, p)` helper.  Texture samplers are declared by the host
from each `SurfaceTexture.uniform`; the fragment samples them but must **not**
redeclare them.

```python
from pytanga.viz import SurfaceShader

shader = SurfaceShader(
    "tinted",
    """
uniform vec3 u_tint;
vec3 surfaceColor(vec3 baseColor, vec3 n, vec3 p) {
    vec3 albedo = texture2D(uTexture, vUv).rgb * u_tint;
    return tangaLight(albedo, n, p);
}
""",
    uniforms={"u_tint": [0.8, 1.0, 1.2]},
)
```

## Standard shaders

`pytanga.viz` ships ready-made shaders that share the same lighting model:
`checkerboard(...)`, `sphere_coloring()`, `grid(...)`, and `gradient(...)`.

```python
from pytanga.viz import SurfaceMaterial, checkerboard, sphere_coloring

viz.add(Sphere(Point(0.0, 0.0, 0.0), 1.0), surface=SurfaceMaterial(shader=sphere_coloring()))
viz.add(Sphere(Point(2.0, 0.0, 0.0), 1.0), surface=SurfaceMaterial(shader=checkerboard()))
```

## Updating shader parameters

Shader uniforms can be changed at runtime **in place** — no entity re-add or
rebuild — over a granular `surface_update` message.  Use the object ref returned
by `viz.new(...)`:

```python
ref = viz.new(Sphere(Point(0.0, 0.0, 0.0), 1.0), surface=SurfaceMaterial(shader=shader))
ref.set_surface_uniform("u_tint", [1.0, 0.5, 0.5])
```

or the `Visualizer` facade by entity id:

```python
viz.set_surface_uniform("sphere_id", "u_tint", [1.0, 0.5, 0.5])
```

The updated value is stored back into the surface style, so a later full
re-serialization (e.g. reconnect) keeps it.

## Shader errors

Shader compile/link failures are reported to the backend as a
`source: "shader"` client-log record; register a handler and show a banner:

```python
async def on_error(record, _event):
    error = record.data.get("error", record.message) if record.data else record.message
    viz.show_banner(f"**Shader error**\n\n```\n{error}\n```", title="Error")

viz.on_shader_error(on_error)
```

See `py/examples/viz/surface/texture_mapping.py` (standard ↔ custom switching
with a twirl slider) and `py/examples/viz/surface/shader_errors.py` (the banner
round-trip).

