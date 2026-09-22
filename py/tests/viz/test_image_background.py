# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the per-pane image background (`CameraView.background_image`)."""

import numpy as np

from pytanga.viz.image import ImageData, ImageDType
from pytanga.viz.views import CameraView, SceneView


def test_background_image_serialize():  # noqa: ANN201
    img = ImageData("bg", data=np.zeros((8, 12, 3), dtype=np.uint8))
    node = SceneView("main", camera_view=CameraView(background_image=img))._serialize()
    assert node["camera_view"]["background_image"] == {
        "id": "bg",
        "width": 12,
        "height": 8,
        "channels": 3,
        "dtype": 0,
        "source": "data",
    }


def test_background_image_omitted_when_none():  # noqa: ANN201
    node = SceneView("main")._serialize()
    assert "camera_view" not in node


def test_background_image_url_metadata():  # noqa: ANN201
    img = ImageData(
        "bg",
        url="https://example.com/a.png",
        width=4,
        height=4,
        channels=3,
        dtype=ImageDType.UINT8,
    )
    node = SceneView("main", camera_view=CameraView(background_image=img))._serialize()
    assert node["camera_view"]["background_image"]["source"] == "url"
    assert node["camera_view"]["background_image"]["url"] == "https://example.com/a.png"
