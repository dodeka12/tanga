# Texture Labels — Overview

**Goal:** Add **programmatic texture labels** to geometric entities using a
**plain text → Canvas → `THREE.CanvasTexture`** pipeline. Supports plain text,
KaTeX math formulas (`$...$` inline, `$$...$$` display), and mixed text+formula content.
Texture labels wrap around spheres (e.g. formula tiled along the equator) and
cover planes (stretched, fitted, or tiled).

**Prerequisites:** Phase 4c (styles), Phase 5 (entity renderers), Phase 12 (KaTeX already loaded)

---

## Architecture

```
User API (convenience):
  viz.add(Sphere(...), tex_label="S₁", tex_label_style=TextureLabelStyle(math_mode=True))
         │
         ▼ _resolve_tex_label_style(global_default, per_kind_default, user_style)
         │   → merged TextureLabelStyle with text="S₁"
         │
         ▼ merged → style=SphereStyle(texture_label=merged_tls)
         │
         ▼ to_dict() → style.texture_label in JSON
         │
WebSocket message ──────────────────────────► JS renderer
                                                  │
                                                  ▼
                                    createTextureLabel(text, style)
                                    ├── math_mode=True  → katex.renderToString()
                                    ├── has $/$$ delims  → split + render segments
                                    └── plain text        → ctx.fillText()
                                                  │
                                                  ▼
                                    THREE.CanvasTexture(canvas)
                                                  │
                                                  ▼
                                    material.map = texture
```

**KaTeX** is already loaded in `viewer.html` (used for annotation/markdown).
**No new CDN dependencies.**

---

## `TextureLabelStyle` Dataclass

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `text` | `str \| None` | `None` | Label content. Plain text, KaTeX formula, or mixed with `$...$`/`$$...$$`. |
| `math_mode` | `bool \| None` | `False` | `True` = entire text is a KaTeX formula. `False` = auto-detect `$` delimiters. |
| `repeat_u` | `float \| None` | `None` | Texture repeat count along U (longitude on sphere, X on plane). |
| `repeat_v` | `float \| None` | `None` | Texture repeat count along V (latitude on sphere, Y on plane). |
| `offset_u` | `float \| None` | `None` | UV offset along U. |
| `offset_v` | `float \| None` | `None` | UV offset along V. Sphere default: 0.25 (equator); Plane default: 0.0. |
| `align` | `str \| None` | `None` | Plane-only: `"stretch"`, `"fit"`, `"repeat"`. Sphere ignores. |
| `background` | `str \| None` | `"#ffffff"` | Canvas background. `None` or `"transparent"` = see-through. |
| `resolution` | `int \| None` | `512` | Canvas width in px (height = width/2). |
| `color` | `str \| None` | `"#000000"` | Text/formula color. |
| `font_size` | `int \| None` | `48` | Font size in px for plain text. Ignored in `math_mode=True`. |

---

## Convenience API — `viz.add(tex_label=...)`

The `add()` method on ``Visualizer`` and ``VizSceneHandle`` gains two new keyword-only
``tex_label`` and ``tex_label_style``, following the same pattern as ``label`` +
``label_style``:

```python
viz.add(
    Sphere(Point(0, 0, 0), 2.0),
    tex_label="S₁",  # ← convenience: just set the text
    tex_label_style=TextureLabelStyle(math_mode=True),  # ← optional: override style fields
)
```

**Resolution order** (same pattern as `label`/`label_style`):
1. If ``tex_label`` is ``None`` → no texture label.
2. Start with the Visualizer's **global default** `TextureLabelStyle` (stored as `self._default_tex_label_style`).
3. Overlay any **per-kind default** from `self._default_tex_label_styles[kind]` (e.g. ``"Sphere"`` may default `offset_v=0.25`).
4. Overlay any fields the user set in ``tex_label_style`` (non-``None`` only).
5. Set `text = tex_label` on the resolved style.
6. If the user also passes an explicit `style=SphereStyle(texture_label=...)`, that takes precedence over the convenience path.

The **Visualizer stores**:
- `self._default_tex_label_style: TextureLabelStyle` — global default (e.g. `font_size=48, background=None`).
- `self._default_tex_label_styles: dict[str, TextureLabelStyle | None]` — per-kind overrides (e.g. `"Sphere"` defaults `offset_v=0.25`, `"Plane"` defaults `offset_v=0.0`).
- `self.default_tex_label_style` — a ``_StyleDict``-wrapped property for user access, mirroring `default_styles`.

The user can configure persistent defaults:

```python
viz.default_tex_label_style["Sphere"] = TextureLabelStyle(
    repeat_u=4, offset_v=0.25, background=None
)
```

---

## Which Entities Get Texture Label Support

| Entity | Field | Phase |
|--------|-------|-------|
| **Sphere** | `SphereStyle.texture_label` | Phase 2, 4 |
| **Plane** | `PlaneStyle.texture_label` | Phase 2, 4 |
| Circle | (future) | — |
| Space | (future) | — |

---

## Sphere-Specific Behavior

- `SphereGeometry` UV: U=0..1 wraps longitude, V=0..1 south-to-north pole
- Equator is at V=0.5 → `offset_v = 0.25` centers a single-tile label at the equator
- Use `repeat_u=4` to tile the label 4 times around the equator
- Use `background=None` to let sphere material color show through

## Plane-Specific Behavior

- `align="stretch"` (default): label fills entire quad
- `align="fit"`: preserves aspect ratio, centered
- `align="repeat"`: tiles with `repeat_u`/`repeat_v`

---

## JSON Wire Format

```json
{
  "id": "s1",
  "kind": "Sphere",
  "center": [0, 0, 0],
  "radius": 2.0,
  "color": "#ffaa00",
  "opacity": 1.0,
  "style": {
    "style_type": "SphereStyle",
    "texture_label": {
      "style_type": "TextureLabelStyle",
      "text": "Radius $$r=2.5$$ cm",
      "math_mode": false,
      "repeat_u": 4,
      "repeat_v": 1,
      "offset_u": 0.0,
      "offset_v": 0.25,
      "background": null,
      "color": "#000000",
      "resolution": 1024,
      "font_size": 48
    }
  }
}
```

When `texture_label` key is absent or `text` is `None` → no texture (plain material color).

---

## Files to Create / Modify

### New Files

| File | Content |
|------|---------|
| `py/pytanga/viz/_styles/_tex_label_style.py` | `TextureLabelStyle` dataclass |
| `py/tests/viz/test_tex_label_style.py` | Serialization tests |
| `py/examples/viz/demo_texture_label_sphere.py` | Sphere demo |
| `py/examples/viz/demo_texture_label_plane.py` | Plane demo |

### Modified Files

| File | Change |
|------|--------|
| `py/pytanga/viz/_styles/_entity_styles.py` | Add `texture_label` to `SphereStyle`, `PlaneStyle` |
| `py/pytanga/viz/_styles/__init__.py` | Export `TextureLabelStyle` |
| `py/pytanga/viz/__init__.py` | Export `TextureLabelStyle` |
| `py/pytanga/viz/visualizer.py` | Add `tex_label` / `tex_label_style` convenience params to `add()`; store `_default_tex_label_style` and per-kind defaults; add `default_tex_label_style` property |
| `py/pytanga/viz/_scene_handle.py` | Add `tex_label` / `tex_label_style` convenience params to `add()` (delegates to Visualizer) |
| `py/pytanga/viz/_style_dict.py` | Add `_make_default_tex_label_style()` and `_make_default_tex_label_styles()` factory functions; add `_resolve_tex_label_style()` |
| `py/pytanga/viz/templates/renderers/utils.js` | Add `createTextureLabel()` + helpers |
| `py/pytanga/viz/templates/renderers/sphere.js` | Apply texture label |
| `py/pytanga/viz/templates/renderers/plane.js` | Apply texture label + align |

---

## Phases

| Phase | File | Summary |
|-------|------|---------|
| **1** | `phase1-tex-style.md` | `TextureLabelStyle` dataclass + serialization |
| **2** | `phase2-entity-styles.md` | Integrate into `SphereStyle`, `PlaneStyle`; Visualizer convenience API |
| **3** | `phase3-frontend-util.md` | `createTextureLabel()` in `utils.js` |
| **4** | `phase4-renderers.md` | Apply in `sphere.js`, `plane.js` renderers |
| **5** | `phase5-tests-examples.md` | Tests + demo scripts |
| **6** | `phase6-docs.md` | Documentation: `texture-labels.md`, update `index.md` & `styles.md` |

---

## Edge Cases

| Scenario | Behavior |
|----------|----------|
| `text` is `None` | No texture; plain material color |
| `texture_label` key absent | No texture |
| `katex` not loaded (CDN fail) | `createTextureLabel()` returns `null`; fallback to plain color |
| Formula render error | KaTeX throws → catch → console.warn → return `null` |
| `repeat_u`/`repeat_v` not set | Default `RepeatWrapping` not applied → texture clamps to edge |
| Very large `resolution` (>2048) | GPU texture limit; works but slow — document recommendation |