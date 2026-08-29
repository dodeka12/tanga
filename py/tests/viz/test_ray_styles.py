# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for RayStyle and the ray-style detection helper."""

import pytest

from pytanga.viz import RayStyle
from pytanga.viz._capabilities import _supports_renderer
from pytanga.viz.serializer import _is_ray_styled


class TestRayStyle:
    def test_to_dict_minimal(self):
        d = RayStyle().to_dict()
        assert d["style_type"] == "RayStyle"
        assert d["bound_padding"] == pytest.approx(0.05)
        assert "color" not in d
        assert "opacity" not in d

    def test_to_dict_with_color_and_opacity(self):
        d = RayStyle(color="#ff0000", opacity=0.5, bound_padding=0.1).to_dict()
        assert d["style_type"] == "RayStyle"
        assert d["color"] == "#ff0000"
        assert d["opacity"] == pytest.approx(0.5)
        assert d["bound_padding"] == pytest.approx(0.1)


class TestIsRayStyled:
    def test_per_entity(self):
        assert _is_ray_styled({"style": RayStyle()}, "Quadric3D", None)

    def test_not_ray_styled(self):
        assert not _is_ray_styled({}, "Sphere", None)
        assert not _is_ray_styled({"style": {}}, "Sphere", None)

    def test_quadric3d_ray_styled_by_default(self):
        # Quadric3D's canonical default style is RayQuadricStyle.
        assert _is_ray_styled({}, "Quadric3D", None)

    def test_per_kind(self):
        styles_map = {"Quadric3D": RayStyle()}
        assert _is_ray_styled({}, "Quadric3D", styles_map)
        assert not _is_ray_styled({}, "Sphere", styles_map)


class TestCapabilities:
    def test_quadric3d_ray_only(self):
        assert _supports_renderer("Quadric3D", "ray")
        assert not _supports_renderer("Quadric3D", "mesh")
        assert not _supports_renderer("Quadric3D", "sdf")

    def test_other_kinds_mesh_sdf(self):
        assert _supports_renderer("Sphere", "mesh")
        assert _supports_renderer("Sphere", "sdf")
        assert not _supports_renderer("Sphere", "ray")
