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


class _FakeTransport:
    """Records JSON + binary sends instead of touching a real socket."""

    def __init__(self) -> None:
        self.json_messages: list[dict] = []
        self.binary_frames: list[bytes] = []

    def send(self, message: dict) -> None:
        self.json_messages.append(message)

    def send_bytes(self, payload: bytes) -> None:
        self.binary_frames.append(payload)


def test_set_background_image_sends_frame_and_message():  # noqa: ANN201
    from pytanga.viz import Visualizer
    from pytanga.viz._image_wire import decode_image_frame

    viz = Visualizer(add_default_axes=False, add_default_grid=False)
    fake = _FakeTransport()
    viz._layout._transport = fake  # type: ignore[attr-defined]
    view = SceneView("main")

    viz.set_background_image(
        view, ImageData("bg", data=np.zeros((8, 12, 3), dtype=np.uint8))
    )

    # One binary frame (bytes sent before the JSON message) + one JSON message.
    assert len(fake.binary_frames) == 1
    decoded = decode_image_frame(fake.binary_frames[0])
    assert decoded["id"] == "bg"
    msg = fake.json_messages[-1]
    assert msg["type"] == "view_background_image"
    assert msg["view_id"] == view.id
    assert msg["image"]["id"] == "bg"
    # Stored so a reconnect re-sends the latest frame.
    assert "bg" in viz._layout._background_frames


def test_set_background_image_creates_camera_view():  # noqa: ANN201
    from pytanga.viz import Visualizer

    viz = Visualizer(add_default_axes=False, add_default_grid=False)
    fake = _FakeTransport()
    viz._layout._transport = fake  # type: ignore[attr-defined]
    view = SceneView("main")  # no camera_view yet
    img = ImageData("bg", data=np.zeros((8, 12, 3), dtype=np.uint8))

    viz.set_background_image(view, img)

    assert view.camera_view is not None
    assert view.camera_view.background_image is img


def test_set_background_image_rejects_non_scene_view():  # noqa: ANN201
    from pytanga.viz import Visualizer
    from pytanga.viz.views import SpacerView

    viz = Visualizer(add_default_axes=False, add_default_grid=False)
    viz._layout._transport = _FakeTransport()  # type: ignore[attr-defined]

    try:
        viz.set_background_image(
            SpacerView(), ImageData("bg", data=np.zeros((2, 2, 3), dtype=np.uint8))
        )
    except TypeError as exc:
        assert "SceneView" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected TypeError for a non-SceneView")


def test_set_background_image_auto_registers_tiled_pyramid():  # noqa: ANN201
    from pytanga.viz import Visualizer

    viz = Visualizer(add_default_axes=False, add_default_grid=False)
    viz._layout._transport = _FakeTransport()  # type: ignore[attr-defined]
    view = SceneView("main")
    img = ImageData("bg", data=np.zeros((5000, 100, 3), dtype=np.uint8))  # auto-tiles
    assert img.source == "tiled"

    viz.set_background_image(view, img)

    assert "bg" in viz._image_pyramids
    assert viz._image_pyramids["bg"] is img.tiled


def test_set_layout_auto_registers_tiled_background():  # noqa: ANN201
    from pytanga.viz import Visualizer

    viz = Visualizer(add_default_axes=False, add_default_grid=False)
    viz._layout._transport = _FakeTransport()  # type: ignore[attr-defined]
    img = ImageData("bg", data=np.zeros((5000, 100, 3), dtype=np.uint8))
    assert img.source == "tiled"

    viz.set_layout(SceneView("main", camera_view=CameraView(background_image=img)))

    assert "bg" in viz._image_pyramids
    assert viz._image_pyramids["bg"] is img.tiled
