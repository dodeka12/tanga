# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the per-entity SDF style classes (viz-sdf-object-model Phase 1)."""

from __future__ import annotations

import pytest
from pytanga.viz import (
    SdfCircleStyle,
    SdfCylinderStyle,
    SdfLineStyle,
    SdfPlaneStyle,
    SdfPointStyle,
    SdfSphereStyle,
    SdfStyle,
)
from pytanga.viz._styles._sdf_style import SDF_STYLE_BY_KIND

_STYLES = [
    (SdfSphereStyle, "SdfSphereStyle", {}),
    (SdfLineStyle, "SdfLineStyle", {"thickness": 1.0}),
    (SdfCircleStyle, "SdfCircleStyle", {"tube_radius": 0.03}),
    (SdfPointStyle, "SdfPointStyle", {"size": 0.08}),
    (SdfCylinderStyle, "SdfCylinderStyle", {}),
    (SdfPlaneStyle, "SdfPlaneStyle", {}),
]


@pytest.mark.parametrize("cls,name,extra", _STYLES)
def test_style_type_and_extra_fields(cls, name, extra) -> None:
    d = cls().to_dict()
    assert d["style_type"] == name
    for key, value in extra.items():
        assert d[key] == value


@pytest.mark.parametrize("cls,name,extra", _STYLES)
def test_derived_styles_are_sdf_styles(cls, name, extra) -> None:
    assert isinstance(cls(), SdfStyle)


@pytest.mark.parametrize("cls,name,extra", _STYLES)
def test_derived_styles_have_no_mesh_only_members(cls, name, extra) -> None:
    style = cls()
    for attr in ("wireframe", "texture_label", "double_sided"):
        assert not hasattr(style, attr), f"{name} must not expose {attr!r}"


def test_registry_maps_entity_kinds() -> None:
    assert SDF_STYLE_BY_KIND == {
        "Sphere": SdfSphereStyle,
        "Line": SdfLineStyle,
        "Circle": SdfCircleStyle,
        "Point": SdfPointStyle,
        "Cylinder": SdfCylinderStyle,
        "Plane": SdfPlaneStyle,
    }


def test_base_sdf_style_style_type_unchanged() -> None:
    assert SdfStyle().to_dict()["style_type"] == "SdfStyle"


def test_derived_style_carries_color_and_opacity() -> None:
    d = SdfLineStyle(color="#ff0000", opacity=0.5).to_dict()
    assert d["color"] == "#ff0000"
    assert d["opacity"] == 0.5
