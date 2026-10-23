# Phase 1 — Python surface material model + style integration

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/architecture/viz-architecture.md` ("Styles" and "New entity kind") and
> the existing `py/pytanga/viz/_styles/` serialization (`_style_to_output` in
> `_styles/__init__.py`).  This phase only **adds** a data model + a style field;
> it does not change the wire contract (the `style` dict already flows to the
> frontend).

## Goal

Add the `py/pytanga/viz/surface/` subpackage (`SurfaceShader`, `SurfaceTexture`,
`SurfaceMaterial`, `surface_material()`, standard shaders), attach a `surface`
field to the seven solid-surface styles, and confirm the serializer emits it.

## Files

- **New** `py/pytanga/viz/surface/__init__.py`
- **New** `py/pytanga/viz/surface/material.py`
- **New** `py/pytanga/viz/surface/standard.py`
- **Edit** `py/pytanga/viz/_styles/_entity_styles.py` — `PlaneStyle`, `SphereStyle`,
  `EllipsoidStyle`, `BoxStyle`, `CylinderStyle`, `ConeStyle`, `DiskStyle`.
- **Edit** `py/pytanga/viz/__init__.py` — export the public names.
- **New** `py/tests/viz/test_surface_material.py`

## Steps

- [x] **1.1 — `surface/material.py`**
  - `@dataclass(frozen=True) SurfaceShader(name, fragment, vertex=None, uniforms=field(default_factory=dict))` with `to_dict()` → `{"name", "fragment", "vertex"?, "uniforms"}` (omit `vertex` when `None`, always emit `uniforms`).
  - `@dataclass SurfaceTexture(image: ImageData, uniform="uTexture0", repeat_u=1.0, repeat_v=1.0, offset_u=0.0, offset_v=0.0, wrap_s="repeat", wrap_t="repeat")` with `to_dict()` → image meta (`id`, `width`, `height`, `channels`, `int(dtype)`, `source`) + `uniform`, `repeat_u/v`, `offset_u/v`, `wrap_s/t`.
  - `@dataclass SurfaceMaterial(shader=None, textures=field(default_factory=list))` with `to_dict()` → `{"shader": shader.to_dict() | None, "textures": [t.to_dict(), ...]}`.
  - `surface_material(obj=None)` normalizes `SurfaceShader` / `SurfaceTexture` / `list[SurfaceTexture]` / `tuple[SurfaceTexture, ...]` / `SurfaceMaterial` into a `SurfaceMaterial`; raise `TypeError` on anything else.
  - Import `ImageData` from `..image` (leaf import, no cycle).

- [x] **1.2 — `surface/standard.py`**
  - `checkerboard(color_a="#ffffff", color_b="#000000", scale=8.0) -> SurfaceShader` — fragment computes `u_color`-independent checker from `vUv * u_scale` (declare `uniform float u_scale;` in `uniforms`).
  - `sphere_coloring() -> SurfaceShader` — color by normalized local position (`vLocalPos`) so a sphere shows a smooth per-axis coloring; document it as the built-in "coloring of a sphere".
  - `grid(line_color="#000000", bg="#ffffff", scale=8.0, line_width=0.05)` and `gradient(a="#ff0000", b="#0000ff", axis="u")` as additional built-ins.
  - Each fragment must **not** declare `main()` or `#version`; it may reference the documented light uniforms and `vUv`/`vNormal`/`vWorldPosition`/`vLocalPos`.

- [x] **1.3 — `surface/__init__.py`**
  - Export `SurfaceShader`, `SurfaceTexture`, `SurfaceMaterial`, `surface_material`, `checkerboard`, `sphere_coloring`, `grid`, `gradient`.

- [x] **1.4 — style `surface` field**
  - Add `surface: SurfaceMaterial | None = None` to `PlaneStyle`, `SphereStyle`, `EllipsoidStyle`, `BoxStyle`, `CylinderStyle`, `ConeStyle`, `DiskStyle`.
  - In each `to_dict()`, emit `result["surface"] = self.surface.to_dict()` only when `self.surface is not None`.
  - Import `SurfaceMaterial` from `..surface.material` (verify no import cycle with `_styles/__init__.py`; if one arises, import lazily inside `to_dict`).

- [x] **1.5 — public exports**
  - Import and add the eight names to `py/pytanga/viz/__init__.py` `__all__` (next to `TextureLabelStyle`/`SdfStyle`).

- [x] **1.6 — tests (`py/tests/viz/test_surface_material.py`)**
  - `SurfaceShader.to_dict()` omits `vertex` when `None`; `SurfaceMaterial.to_dict()` emits `shader: None` + empty `textures` for a bare material.
  - `surface_material()` normalizes a bare `SurfaceShader` / `SurfaceTexture` / list / `None`.
  - `SurfaceTexture.to_dict()` matches the wire meta shape (`id`, `width`, `height`, `channels`, `dtype`, `source`, `uniform`, wraps).
  - `SphereStyle(surface=surface_material(checkerboard())).to_dict()["surface"]["shader"]["name"] == "checkerboard"`.
  - Standard shaders are non-empty strings and carry no `main()`/`#version`.

## Validation

```bash
uv run pytest py/tests/viz/test_surface_material.py -q
uv run ruff check py/pytanga/viz/surface py/pytanga/viz/_styles/_entity_styles.py
uv run ty check
```

## Notes

- `_style_to_output` (in `_styles/__init__.py`) already merges `to_dict()` output and
  overlays non-`None` user fields, so `surface` reaches `ent.style.surface` with no
  serializer change — verify with a quick `serialize_entity` smoke in the test.
