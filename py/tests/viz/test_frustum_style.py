# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for ``FrustumStyle``."""

from pytanga.viz import FrustumStyle


def test_frustum_style_defaults():  # noqa: ANN201
    d = FrustumStyle().to_dict()
    assert d == {"style_type": "FrustumStyle"}


def test_frustum_style_full():  # noqa: ANN201
    d = FrustumStyle(
        color="#88ccff", opacity=0.9, fill=True, fill_opacity=0.3, thickness=2.0
    ).to_dict()
    assert d == {
        "style_type": "FrustumStyle",
        "color": "#88ccff",
        "opacity": 0.9,
        "fill": True,
        "fill_opacity": 0.3,
        "thickness": 2.0,
    }
