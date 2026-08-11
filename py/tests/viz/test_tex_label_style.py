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
        assert "background" not in d  # None is omitted
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