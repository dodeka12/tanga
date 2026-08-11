# Phase 2 — Integrate `TextureLabelStyle` into Entity Styles

**Prerequisites:** Phase 1 (`TextureLabelStyle` dataclass exists and is importable)

**Goal:** Add an optional `texture_label` field to `SphereStyle` and `PlaneStyle`.
When `texture_label` is `None` (the default), no texture is applied — the entity
renders with its plain material color. When set, the serializer includes
`texture_label` in the style dict under the entity's `style` key.

---

## 1. Motivation

`SphereStyle` and `PlaneStyle` currently control color, opacity, wireframe, and
extent — but have no mechanism for a surface texture label. By adding
`texture_label: TextureLabelStyle | None = None`, users can optionally apply
formulas, text, or mixed labels directly onto the entity surface.

Circle and Space are deferred to a future phase (their UV mappings are more complex).

---

## 2. Changes to `_entity_styles.py`

### 2.1 Import

Add at the top of `py/pytanga/viz/_styles/_entity_styles.py`:

```python
from ._tex_label_style import TextureLabelStyle
```

### 2.2 `SphereStyle`

Add the field and update `to_dict()`:

```python
@dataclass
class SphereStyle(VizStyle):
    """Visual style for :class:`~pytanga.geometry.Sphere`.

    Attributes:
        wireframe: When ``True``, a wireframe cage is drawn over the
            sphere surface.
        wireframe_dash: Optional :class:`WireframeDashPattern` for dashed
            wireframe lines.  ``None`` defaults to solid lines.
        wireframe_color: Optional override color for wireframe lines.
            ``None`` uses the entity's main color.
        wireframe_opacity: Optional opacity for wireframe lines (0..1).
            ``None`` defaults to fully opaque.
        texture_label: Optional :class:`TextureLabelStyle` for a text
            or formula label rendered onto the sphere surface.  When
            ``None``, no texture is applied.  Use ``offset_v=0.25`` to
            center the label at the equator.
    """

    color: str | None = None
    opacity: float | None = None
    wireframe: bool | None = None
    wireframe_dash: WireframeDashPattern | None = None
    wireframe_color: str | None = None
    wireframe_opacity: float | None = None
    texture_label: TextureLabelStyle | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"style_type": "SphereStyle"}
        if self.color is not None:
            result["color"] = self.color
        if self.opacity is not None:
            result["opacity"] = self.opacity
        if self.wireframe is not None:
            result["wireframe"] = self.wireframe
        if self.wireframe_dash is not None:
            result["wireframe_dash"] = self.wireframe_dash.to_dict()
        if self.wireframe_color is not None:
            result["wireframe_color"] = self.wireframe_color
        if self.wireframe_opacity is not None:
            result["wireframe_opacity"] = self.wireframe_opacity
        if self.texture_label is not None:
            result["texture_label"] = self.texture_label.to_dict()
        return result
```

### 2.3 `PlaneStyle`

Add the field and update `to_dict()`:

```python
@dataclass
class PlaneStyle(VizStyle):
    """Visual style for :class:`~pytanga.geometry.Plane`.

    Attributes:
        wireframe: When ``True``, a wireframe cage is drawn over the
            plane surface.
        wireframe_dash: Optional :class:`WireframeDashPattern` for dashed
            wireframe lines.  ``None`` defaults to solid lines.
        wireframe_color: Optional override color for wireframe lines.
            ``None`` uses the entity's main color.
        wireframe_opacity: Optional opacity for wireframe lines (0..1).
            ``None`` defaults to fully opaque.
        texture_label: Optional :class:`TextureLabelStyle` for a text
            or formula label rendered onto the plane surface.  When
            ``None``, no texture is applied.  Use ``align`` to control
            layout (``"stretch"``, ``"fit"``, ``"repeat"``).
    """

    color: str | None = None
    opacity: float | None = None
    extent: float | None = None
    wireframe: bool | None = None
    wireframe_dash: WireframeDashPattern | None = None
    wireframe_color: str | None = None
    wireframe_opacity: float | None = None
    texture_label: TextureLabelStyle | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"style_type": "PlaneStyle"}
        if self.color is not None:
            result["color"] = self.color
        if self.opacity is not None:
            result["opacity"] = self.opacity
        if self.extent is not None:
            result["extent"] = self.extent
        if self.wireframe is not None:
            result["wireframe"] = self.wireframe
        if self.wireframe_dash is not None:
            result["wireframe_dash"] = self.wireframe_dash.to_dict()
        if self.wireframe_color is not None:
            result["wireframe_color"] = self.wireframe_color
        if self.wireframe_opacity is not None:
            result["wireframe_opacity"] = self.wireframe_opacity
        if self.texture_label is not None:
            result["texture_label"] = self.texture_label.to_dict()
        return result
```

---

## 3. Changes to `_styles/__init__.py`

### 3.1 Canonical Defaults

Update the `_DEFAULT_STYLE_FOR_KIND` dict entries for `"Sphere"` and `"Plane"`.
The `texture_label` field defaults to `None` (no texture), so existing entries
do not need to change — but explicitly noting `texture_label=None` makes the
intent clear:

```python
_DEFAULT_STYLE_FOR_KIND: dict[str, VizStyle] = {
    # ... existing entries unchanged ...
    "Sphere": SphereStyle(color="#ffaa00", opacity=0.4, wireframe=True),
    "Plane": PlaneStyle(color="#4488ff", opacity=0.3, extent=10.0),
    # ...
}
```

No changes needed — `texture_label=None` is the dataclass default, and the
canonical defaults do not set it.

### 3.2 No Changes to `_default_style_for()` or `_style_to_output()`

These functions work with `VizStyle` instances generically. `texture_label`
is just another field on the style dataclass — it gets serialized via `to_dict()`
when the style is merged and sent to the frontend.

---

## 4. No Changes to `serializer.py`

The serializer's `_apply_defaults()` already merges style dicts via
`_style_to_output()`. The `texture_label` key flows through automatically:

```python
def _apply_defaults(props, kind, builtin, *, styles_map=None):
    # ...
    merged_style = _style_to_output(props.get("style"), kind, styles_map=styles_map)
    result["style"] = merged_style
    # ...
```

When a user passes `style=SphereStyle(texture_label=TextureLabelStyle(...))`,
the style object's `to_dict()` includes `"texture_label": {...}`, which is
merged into the output JSON automatically.

---

## 5. JSON Wire Format (Example)

### Sphere with texture label

```json
{
  "id": "s1",
  "kind": "Sphere",
  "center": [0.0, 0.0, 0.0],
  "radius": 2.0,
  "color": "#ffaa00",
  "opacity": 1.0,
  "style": {
    "style_type": "SphereStyle",
    "color": "#ffaa00",
    "opacity": 1.0,
    "wireframe": true,
    "texture_label": {
      "style_type": "TextureLabelStyle",
      "text": "\\mathcal{S}_1",
      "math_mode": true,
      "repeat_u": 4,
      "repeat_v": 1,
      "offset_v": 0.25,
      "background": null,
      "resolution": 1024
    }
  }
}
```

### Plane with texture label

```json
{
  "id": "p1",
  "kind": "Plane",
  "point": [0.0, 0.0, 3.0],
  "normal": [0.0, 0.0, 1.0],
  "extent": 10.0,
  "color": "#4488ff",
  "opacity": 0.3,
  "style": {
    "style_type": "PlaneStyle",
    "color": "#4488ff",
    "opacity": 0.3,
    "extent": 10.0,
    "texture_label": {
      "style_type": "TextureLabelStyle",
      "text": "Plane at $$z=3$$",
      "math_mode": false,
      "align": "fit",
      "background": "#ffffff",
      "color": "#333333",
      "font_size": 36
    }
  }
}
```

### Sphere without texture label (current behavior)

```json
{
  "id": "s2",
  "kind": "Sphere",
  "center": [5.0, 0.0, 0.0],
  "radius": 1.0,
  "color": "#44ff44",
  "opacity": 0.8,
  "style": {
    "style_type": "SphereStyle",
    "color": "#44ff44",
    "opacity": 0.8,
    "wireframe": false
  }
}
```

No `texture_label` key → frontend renders with plain material color (unchanged behavior).

---

## 6. Implementation Checklist

- [ ] Import `TextureLabelStyle` in `_entity_styles.py`
- [ ] Add `texture_label: TextureLabelStyle | None = None` to `SphereStyle`
- [ ] Update `SphereStyle.to_dict()` to serialize `texture_label` when not `None`
- [ ] Add `texture_label: TextureLabelStyle | None = None` to `PlaneStyle`
- [ ] Update `PlaneStyle.to_dict()` to serialize `texture_label` when not `None`
- [ ] Verify existing tests still pass (texture_label=None is the default, no behavioral change)

---

## 7. Verification

- [ ] `SphereStyle().to_dict()` → no `"texture_label"` key
- [ ] `SphereStyle(texture_label=TextureLabelStyle(text="S₁")).to_dict()` → includes `"texture_label": {"style_type": "TextureLabelStyle", "text": "S₁", ...}`
- [ ] `PlaneStyle().to_dict()` → no `"texture_label"` key
- [ ] `PlaneStyle(texture_label=TextureLabelStyle(text="P", align="fit")).to_dict()` → includes `"texture_label": {...}`
- [ ] `from pytanga.viz import SphereStyle, PlaneStyle, TextureLabelStyle` works
- [ ] All existing viz tests pass (no regression)