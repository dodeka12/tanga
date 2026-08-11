# Phase 5 — Tests & Examples

**Prerequisites:** Phases 1–4 complete (full pipeline: Python → JSON → JS → textured mesh)

**Goal:** Verify the texture label pipeline end-to-end with Python serialization tests
and visual demo scripts for spheres and planes.

---

## 1. Python Tests

### 1.1 New File: `py/tests/viz/test_tex_label_style.py`

```python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for TextureLabelStyle serialization and integration with entity styles."""

from __future__ import annotations

from pytanga.viz._styles import TextureLabelStyle, SphereStyle, PlaneStyle


class TestTextureLabelStyle:
    """Tests for the TextureLabelStyle dataclass."""

    def test_default_construction(self):
        """A default TextureLabelStyle has sensible defaults."""
        tls = TextureLabelStyle()
        assert tls.text is None
        assert tls.math_mode is False
        assert tls.repeat_u is None
        assert tls.repeat_v is None
        assert tls.offset_u is None
        assert tls.offset_v is None
        assert tls.align is None
        assert tls.background == "#ffffff"
        assert tls.resolution == 512
        assert tls.color == "#000000"
        assert tls.font_size == 48

    def test_to_dict_defaults(self):
        """to_dict() includes only non-None fields with defaults."""
        tls = TextureLabelStyle()
        d = tls.to_dict()
        assert d["style_type"] == "TextureLabelStyle"
        assert d["math_mode"] is False
        assert d["background"] == "#ffffff"
        assert d["resolution"] == 512
        assert d["color"] == "#000000"
        assert d["font_size"] == 48
        # None fields are omitted
        assert "text" not in d
        assert "repeat_u" not in d
        assert "repeat_v" not in d
        assert "offset_u" not in d
        assert "offset_v" not in d
        assert "align" not in d

    def test_to_dict_full_math_mode(self):
        """Full math mode with equator offset and repeating."""
        tls = TextureLabelStyle(
            text=r"\mathcal{S}_1",
            math_mode=True,
            repeat_u=4,
            repeat_v=1,
            offset_v=0.25,
            background=None,
            resolution=1024,
        )
        d = tls.to_dict()
        assert d["style_type"] == "TextureLabelStyle"
        assert d["text"] == "\\mathcal{S}_1"
        assert d["math_mode"] is True
        assert d["repeat_u"] == 4
        assert d["repeat_v"] == 1
        assert d["offset_v"] == 0.25
        assert d["background"] is None
        assert d["resolution"] == 1024

    def test_to_dict_plain_text(self):
        """Plain text mode with custom font size."""
        tls = TextureLabelStyle(
            text="Hello World",
            font_size=36,
            color="#333333",
        )
        d = tls.to_dict()
        assert d["text"] == "Hello World"
        assert d["math_mode"] is False
        assert d["font_size"] == 36
        assert d["color"] == "#333333"

    def test_to_dict_mixed_mode(self):
        """Mixed text+formula mode."""
        tls = TextureLabelStyle(
            text="Radius $$r=2.5$$ cm",
            math_mode=False,
            align="fit",
            background="#ffffff",
        )
        d = tls.to_dict()
        assert d["text"] == "Radius $$r=2.5$$ cm"
        assert d["math_mode"] is False
        assert d["align"] == "fit"

    def test_to_dict_null_text(self):
        """When text is explicitly None, it is omitted."""
        tls = TextureLabelStyle(text=None, math_mode=True)
        d = tls.to_dict()
        assert "text" not in d


class TestEntityStyleIntegration:
    """Tests for texture_label field on entity styles."""

    def test_sphere_style_no_texture_label(self):
        """SphereStyle without texture_label omits the key."""
        style = SphereStyle(color="#ffaa00", opacity=0.4)
        d = style.to_dict()
        assert d["style_type"] == "SphereStyle"
        assert "texture_label" not in d

    def test_sphere_style_with_texture_label(self):
        """SphereStyle with texture_label includes it in output."""
        tls = TextureLabelStyle(text="S₁", math_mode=True, offset_v=0.25)
        style = SphereStyle(
            color="#ffaa00",
            opacity=0.4,
            wireframe=True,
            texture_label=tls,
        )
        d = style.to_dict()
        assert d["style_type"] == "SphereStyle"
        assert "texture_label" in d
        assert d["texture_label"]["style_type"] == "TextureLabelStyle"
        assert d["texture_label"]["text"] == "S₁"
        assert d["texture_label"]["math_mode"] is True
        assert d["texture_label"]["offset_v"] == 0.25

    def test_plane_style_no_texture_label(self):
        """PlaneStyle without texture_label omits the key."""
        style = PlaneStyle(color="#4488ff", opacity=0.3, extent=10.0)
        d = style.to_dict()
        assert d["style_type"] == "PlaneStyle"
        assert "texture_label" not in d

    def test_plane_style_with_texture_label(self):
        """PlaneStyle with texture_label includes it in output."""
        tls = TextureLabelStyle(
            text="Plane $$z=3$$",
            math_mode=False,
            align="fit",
            background="#ffffff",
        )
        style = PlaneStyle(
            color="#4488ff",
            opacity=0.3,
            texture_label=tls,
        )
        d = style.to_dict()
        assert d["style_type"] == "PlaneStyle"
        assert "texture_label" in d
        assert d["texture_label"]["text"] == "Plane $$z=3$$"
        assert d["texture_label"]["align"] == "fit"
```

---

## 2. Demo Scripts

### 2.1 New File: `py/examples/viz/demo_texture_label_sphere.py`

```python
# SPDX-License-Identifier: Apache-2.2
# Copyright 2021 Christian Perwass

"""Demo: Texture labels on spheres using plain text and KaTeX formulas.

Run::

    uv run python py/examples/viz/demo_texture_label_sphere.py
"""

from pytanga.geometry.entities import Sphere, Point
from pytanga.viz import Visualizer, SphereStyle, TextureLabelStyle


def main():
    viz = Visualizer(port=8765, open_browser=True)
    viz.set_title("Texture Labels on Spheres")

    # ── Sphere with plain text label ──
    viz.add(
        Sphere(Point(-3, 0, 0), 2.0),
        style=SphereStyle(
            color="#4488ff",
            opacity=0.6,
            wireframe=True,
            texture_label=TextureLabelStyle(
                text="Sphere A",
                repeat_u=2,
                repeat_v=1,
                offset_v=0.25,
                background=None,
                color="#ffffff",
                font_size=64,
            ),
        ),
    )

    # ── Sphere with KaTeX formula label ──
    viz.add(
        Sphere(Point(0, 0, 0), 2.0),
        style=SphereStyle(
            color="#ff8844",
            opacity=0.6,
            wireframe=True,
            texture_label=TextureLabelStyle(
                text=r"\mathcal{S}_1",
                math_mode=True,
                repeat_u=4,
                repeat_v=1,
                offset_v=0.25,
                background=None,
                color="#000000",
                resolution=1024,
            ),
        ),
    )

    # ── Sphere with mixed text + embedded formula ──
    viz.add(
        Sphere(Point(3, 0, 0), 2.0),
        style=SphereStyle(
            color="#44ff44",
            opacity=0.6,
            wireframe=True,
            texture_label=TextureLabelStyle(
                text="Radius $$r=2$$",
                math_mode=False,
                repeat_u=2,
                repeat_v=1,
                offset_v=0.25,
                background=None,
                color="#000000",
                font_size=48,
                resolution=1024,
            ),
        ),
    )

    # ── Reference sphere without texture label ──
    viz.add(
        Sphere(Point(0, 4, 0), 1.0),
        style=SphereStyle(
            color="#ffaa00",
            opacity=0.4,
            wireframe=True,
        ),
    )

    print("Starting viewer — open your browser to http://localhost:8765")
    viz.run()


if __name__ == "__main__":
    main()
```

### 2.2 New File: `py/examples/viz/demo_texture_label_plane.py`

```python
# SPDX-License-Identifier: Apache-2.2
# Copyright 2021 Christian Perwass

"""Demo: Texture labels on planes with different align modes.

Run::

    uv run python py/examples/viz/demo_texture_label_plane.py
"""

from pytanga.geometry.entities import Plane, Point, Direction
from pytanga.viz import Visualizer, PlaneStyle, TextureLabelStyle


def main():
    viz = Visualizer(port=8766, open_browser=True)
    viz.set_title("Texture Labels on Planes")

    # ── Plane with "stretch" align (fills the quad) ──
    viz.add(
        Plane(Point(0, 0, 0), Direction(0, 0, 1)),
        style=PlaneStyle(
            color="#4488ff",
            opacity=0.3,
            extent=5.0,
            texture_label=TextureLabelStyle(
                text="Stretch Mode",
                align="stretch",
                background="#ffffff",
                color="#333333",
                font_size=48,
            ),
        ),
    )

    # ── Plane with "fit" align (preserves aspect ratio) ──
    viz.add(
        Plane(Point(0, 0, 3), Direction(0, 0, 1)),
        style=PlaneStyle(
            color="#44ff44",
            opacity=0.3,
            extent=4.0,
            texture_label=TextureLabelStyle(
                text="Fit Mode",
                align="fit",
                background="#ffffff",
                color="#333333",
                font_size=48,
            ),
        ),
    )

    # ── Plane with "repeat" align (tiled) ──
    viz.add(
        Plane(Point(0, 0, 6), Direction(0, 0, 1)),
        style=PlaneStyle(
            color="#ff8844",
            opacity=0.3,
            extent=4.0,
            texture_label=TextureLabelStyle(
                text="Tile",
                align="repeat",
                repeat_u=3,
                repeat_v=3,
                background=None,
                color="#000000",
                font_size=48,
            ),
        ),
    )

    # ── Plane with mixed text + formula ──
    viz.add(
        Plane(Point(-6, 0, 3), Direction(1, 0, 0)),
        style=PlaneStyle(
            color="#ff44ff",
            opacity=0.3,
            extent=4.0,
            texture_label=TextureLabelStyle(
                text="Plane $$z=3$$ with $$\\mathbf{\\hat{n}}$$",
                math_mode=False,
                align="fit",
                background="#ffffff",
                color="#333333",
                font_size=36,
            ),
        ),
    )

    # ── Reference plane without texture label ──
    viz.add(
        Plane(Point(0, 0, 9), Direction(0, 0, 1)),
        style=PlaneStyle(
            color="#888888",
            opacity=0.15,
            extent=5.0,
            wireframe=True,
        ),
    )

    print("Starting viewer — open your browser to http://localhost:8766")
    viz.run()


if __name__ == "__main__":
    main()
```

---

## 3. Test Checklist

### 3.1 Python Serialization Tests

- [ ] `TextureLabelStyle().to_dict()` → correct defaults, no `None` keys
- [ ] `TextureLabelStyle(text="abc", math_mode=True, ...)` → all fields present
- [ ] `TextureLabelStyle(text=None)` → `text` key omitted
- [ ] `SphereStyle().to_dict()` → no `texture_label` key
- [ ] `SphereStyle(texture_label=TextureLabelStyle(...)).to_dict()` → `texture_label` present with correct nested dict
- [ ] `PlaneStyle(texture_label=TextureLabelStyle(...)).to_dict()` → `texture_label` present with correct nested dict

### 3.2 Visual Verification

- [ ] **`demo_texture_label_sphere.py`**: Open browser, verify:
  - Left sphere: "Sphere A" in white text, repeated 2× around equator
  - Center sphere: `S₁` KaTeX formula, repeated 4× around equator
  - Right sphere: "Radius r=2" with `r=2` rendered as math
  - Top sphere: plain wireframe, no texture (reference)
  - Orbit around to verify text wraps correctly at equator
- [ ] **`demo_texture_label_plane.py`**: Open browser, verify:
  - Bottom plane: "Stretch Mode" fills entire quad (may appear stretched horizontally)
  - Middle plane: "Fit Mode" centered with space on sides
  - Top plane: "Tile" repeated 3×3 grid
  - Side plane: mixed text+formula, readable
  - Topmost plane: plain wireframe, no texture (reference)

### 3.3 Edge Cases

- [ ] Sphere with `text=None` renders as plain colored sphere (no error)
- [ ] No `texture_label` key in style → plain material (backward compatible)
- [ ] `katex` not loaded in browser → formula falls back gracefully (console warning, plain text or empty texture)
- [ ] Very long text → should wrap within the canvas (plain text mode word-wraps)
- [ ] `resolution=256` → label is low-res but renders
- [ ] `resolution=2048` → label is sharp, performance acceptable
- [ ] `background=None` on sphere → sphere color shows through the label background
- [ ] `background="#ff0000"` → red background visible behind the label

---

## 4. Test Runner

Run with:

```bash
# Python unit tests
uv run pytest py/tests/viz/test_tex_label_style.py -v

# Full viz test suite (ensure no regressions)
uv run pytest py/tests/viz/ -v

# Demo scripts (manual visual verification)
uv run python py/examples/viz/demo_texture_label_sphere.py
uv run python py/examples/viz/demo_texture_label_plane.py
```

---

## 5. Implementation Checklist

- [ ] Create `py/tests/viz/test_tex_label_style.py`
- [ ] Create `py/examples/viz/demo_texture_label_sphere.py`
- [ ] Create `py/examples/viz/demo_texture_label_plane.py`
- [ ] Run `pytest py/tests/viz/test_tex_label_style.py -v` — all tests pass
- [ ] Run `pytest py/tests/viz/ -v` — no regressions in existing tests
- [ ] Run `python py/examples/viz/demo_texture_label_sphere.py` — browser opens, spheres show labels
- [ ] Run `python py/examples/viz/demo_texture_label_plane.py` — browser opens, planes show labels