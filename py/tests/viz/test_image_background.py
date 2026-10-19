# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the per-pane image background (`CameraView.background_image`)."""

import numpy as np
import pytest

from pytanga.viz.image import ImageData, ImageDType, ImageLayerStyle
from pytanga.viz.views import CameraView, SceneView


def test_background_image_serialize():  # noqa: ANN201
    img = ImageData("bg", data=np.zeros((8, 12, 3), dtype=np.uint8))
    node = SceneView("main", camera_view=CameraView(background_image=img))._serialize()
    meta = node["camera_view"]["background_image"]
    assert meta["version"] == img.version
    assert meta["shader"] == {"fragment": None, "vertex": None}
    assert meta["uniforms"]["u_brightness"] == 0.0
    assert meta["uniforms"]["u_contrast"] == 1.0
    assert meta["uniforms"]["u_midpoint"] == 0.5
    assert meta["uniforms"]["u_mode"] == 1  # 3 channels → RGB
    assert meta["uniforms"]["u_value_max"] == 1.0  # uint8 → [0, 1]
    assert meta["images"][0]["id"] == "bg"
    assert meta["images"][0]["enabled"] == 1
    assert meta["max_layers"] == 8
    del meta["version"], meta["shader"], meta["uniforms"], meta["images"], meta["max_layers"]
    assert meta == {
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
    assert view.camera_view.background_image.primary_image is img


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


def test_set_layout_same_instance_sends_frame_once():  # noqa: ANN201
    from pytanga.viz import Visualizer

    viz = Visualizer(add_default_axes=False, add_default_grid=False)
    fake = _FakeTransport()
    viz._layout._transport = fake  # type: ignore[attr-defined]
    img = ImageData("bg", data=np.zeros((8, 12, 3), dtype=np.uint8))
    view = SceneView("main", camera_view=CameraView(background_image=img))

    viz.set_layout(view)
    viz.set_layout(view)

    assert len(fake.binary_frames) == 1


def test_set_layout_update_bumps_version_and_resends():  # noqa: ANN201
    from pytanga.viz import Visualizer

    viz = Visualizer(add_default_axes=False, add_default_grid=False)
    fake = _FakeTransport()
    viz._layout._transport = fake  # type: ignore[attr-defined]
    img = ImageData("bg", data=np.zeros((8, 12, 3), dtype=np.uint8))
    view = SceneView("main", camera_view=CameraView(background_image=img))

    viz.set_layout(view)
    img.update(data=np.ones((8, 12, 3), dtype=np.uint8))
    viz.set_layout(view)

    assert len(fake.binary_frames) == 2
    assert viz._layout._background_versions["bg"] == img.version


def test_set_layout_new_instance_resends():  # noqa: ANN201
    from pytanga.viz import Visualizer

    viz = Visualizer(add_default_axes=False, add_default_grid=False)
    fake = _FakeTransport()
    viz._layout._transport = fake  # type: ignore[attr-defined]
    viz.set_layout(
        SceneView(
            "main",
            camera_view=CameraView(
                background_image=ImageData("bg", data=np.zeros((8, 12, 3), dtype=np.uint8))
            ),
        )
    )

    viz.set_layout(
        SceneView(
            "main",
            camera_view=CameraView(
                background_image=ImageData("bg", data=np.zeros((8, 12, 3), dtype=np.uint8))
            ),
        )
    )

    assert len(fake.binary_frames) == 2


def test_set_layout_removed_prunes_cache():  # noqa: ANN201
    from pytanga.viz import Visualizer

    viz = Visualizer(add_default_axes=False, add_default_grid=False)
    fake = _FakeTransport()
    viz._layout._transport = fake  # type: ignore[attr-defined]
    img = ImageData("bg", data=np.zeros((8, 12, 3), dtype=np.uint8))
    viz.set_layout(SceneView("main", camera_view=CameraView(background_image=img)))
    assert "bg" in viz._layout._background_frames

    viz.set_layout(SceneView("main"))

    assert "bg" not in viz._layout._background_frames
    assert "bg" not in viz._layout._background_versions


def test_set_background_uniform_sends_message():  # noqa: ANN201
    from pytanga.viz import Visualizer

    viz = Visualizer(add_default_axes=False, add_default_grid=False)
    fake = _FakeTransport()
    viz._layout._transport = fake  # type: ignore[attr-defined]
    view = SceneView(
        "main",
        camera_view=CameraView(
            background_image=ImageData("bg", data=np.zeros((8, 12, 3), dtype=np.uint8))
        ),
    )

    before = len(fake.binary_frames)
    viz.set_background_uniform(view, "u_contrast", 1.2)

    assert len(fake.binary_frames) == before  # no pixel bytes
    msg = fake.json_messages[-1]
    assert msg["type"] == "view_background_uniforms"
    assert msg["view_id"] == view.id
    assert msg["uniforms"] == {"u_contrast": 1.2}


def test_register_background_shader_re_pushes():  # noqa: ANN201
    from pytanga.viz import Visualizer

    viz = Visualizer(add_default_axes=False, add_default_grid=False)
    fake = _FakeTransport()
    viz._layout._transport = fake  # type: ignore[attr-defined]
    view = SceneView(
        "main",
        camera_view=CameraView(
            background_image=ImageData("bg", data=np.zeros((8, 12, 3), dtype=np.uint8))
        ),
    )

    viz.register_background_shader(view, "void main() {}", "vertex")

    msg = fake.json_messages[-1]
    assert msg["type"] == "view_background_image"
    assert msg["image"]["shader"] == {"fragment": "void main() {}", "vertex": "vertex"}


def test_set_background_image_preserves_shader_and_uniforms():  # noqa: ANN201
    from pytanga.viz import Visualizer

    viz = Visualizer(add_default_axes=False, add_default_grid=False)
    fake = _FakeTransport()
    viz._layout._transport = fake  # type: ignore[attr-defined]
    view = SceneView("main")
    viz.set_background_image(view, ImageData("bg", data=np.zeros((8, 12, 3), dtype=np.uint8)))
    viz.register_background_shader(view, "frag")
    viz.set_background_uniform(view, "u_contrast", 1.5)

    img2 = ImageData("bg", data=np.ones((8, 12, 3), dtype=np.uint8))
    viz.set_background_image(view, img2)

    image_view = view.camera_view.background_image
    assert image_view.primary_image is img2
    assert image_view.shader["fragment"] == "frag"
    assert image_view.uniforms["u_contrast"] == 1.5


def test_multi_layer_background_serializes_images():  # noqa: ANN201
    from pytanga.viz import ImageView

    view = ImageView("bg")
    view.set_image(ImageData("img1", data=np.zeros((8, 12, 3), dtype=np.uint8)))
    view.add_layer(ImageData("img2", data=np.zeros((4, 6), dtype=np.uint16)))

    node = SceneView("main", camera_view=CameraView(background_image=view))._serialize()
    images = node["camera_view"]["background_image"]["images"]

    assert [img["id"] for img in images] == ["img1", "img2"]
    assert images[1]["value_max"] == 65535.0  # uint16
    assert images[1]["enabled"] == 1


def test_multi_layer_background_sends_two_frames():  # noqa: ANN201
    from pytanga.viz import ImageView, Visualizer

    viz = Visualizer(add_default_axes=False, add_default_grid=False)
    fake = _FakeTransport()
    viz._layout._transport = fake  # type: ignore[attr-defined]

    view = ImageView("bg")
    view.set_image(ImageData("img1", data=np.zeros((8, 12, 3), dtype=np.uint8)))
    view.add_layer(ImageData("img2", data=np.zeros((8, 12, 3), dtype=np.uint8)))
    viz.set_layout(SceneView("main", camera_view=CameraView(background_image=view)))

    assert len(fake.binary_frames) == 2


def test_tiled_background_emits_images_with_tiled_extras():  # noqa: ANN201
    img = ImageData("bg", data=np.zeros((5000, 100, 3), dtype=np.uint8))  # auto-tiles
    assert img.source == "tiled"

    node = SceneView("main", camera_view=CameraView(background_image=img))._serialize()
    images = node["camera_view"]["background_image"]["images"]

    assert len(images) == 1
    assert images[0]["source"] == "tiled"
    assert images[0]["tile_version"] == 0
    assert "tile_size" in images[0]
    assert "levels" in images[0]


def test_bound_set_layer_style_pushes_uniform_patch():  # noqa: ANN201
    from pytanga.viz import ImageView, Visualizer

    viz = Visualizer(add_default_axes=False, add_default_grid=False)
    fake = _FakeTransport()
    viz._layout._transport = fake  # type: ignore[attr-defined]

    bg = ImageView("bg")
    bg.set_image(ImageData("img1", data=np.zeros((8, 12, 3), dtype=np.uint8)))
    bg.add_layer(ImageData("img2", data=np.zeros((8, 12), dtype=np.uint8)))
    view = SceneView("main", camera_view=CameraView(background_image=bg))
    viz.set_layout(view)
    fake.json_messages.clear()

    bg.set_layer_style(1, ImageLayerStyle(opacity=0.3))

    uniforms_msgs = [
        m for m in fake.json_messages if m["type"] == "view_background_uniforms"
    ]
    assert len(uniforms_msgs) == 1
    assert uniforms_msgs[0]["view_id"] == view.id
    assert uniforms_msgs[0]["uniforms"] == {"u_layer1_opacity": 0.3}


def test_bound_set_layer_pushes_only_changed_frame():  # noqa: ANN201
    from pytanga.viz import ImageView, Visualizer
    from pytanga.viz._image_wire import decode_image_frame

    viz = Visualizer(add_default_axes=False, add_default_grid=False)
    fake = _FakeTransport()
    viz._layout._transport = fake  # type: ignore[attr-defined]

    bg = ImageView("bg")
    bg.set_image(ImageData("img1", data=np.zeros((8, 12, 3), dtype=np.uint8)))
    bg.add_layer(ImageData("img2", data=np.zeros((8, 12), dtype=np.uint8)))
    view = SceneView("main", camera_view=CameraView(background_image=bg))
    viz.set_layout(view)
    fake.binary_frames.clear()
    fake.json_messages.clear()

    bg.set_layer(1, ImageData("img3", data=np.ones((8, 12), dtype=np.uint8)))

    assert len(fake.binary_frames) == 1
    assert decode_image_frame(fake.binary_frames[0])["id"] == "img3"

    img_msgs = [
        m for m in fake.json_messages if m["type"] == "view_background_image"
    ]
    assert len(img_msgs) == 1
    assert img_msgs[0]["view_id"] == view.id
    assert img_msgs[0]["image"]["images"][0]["id"] == "img1"
    assert img_msgs[0]["image"]["images"][1]["id"] == "img3"


def test_bound_remove_layer_updates_meta_and_prunes_cache():  # noqa: ANN201
    from pytanga.viz import ImageView, Visualizer

    viz = Visualizer(add_default_axes=False, add_default_grid=False)
    fake = _FakeTransport()
    viz._layout._transport = fake  # type: ignore[attr-defined]

    bg = ImageView("bg")
    bg.set_image(ImageData("img1", data=np.zeros((8, 12, 3), dtype=np.uint8)))
    bg.add_layer(ImageData("img2", data=np.zeros((8, 12), dtype=np.uint8)))
    view = SceneView("main", camera_view=CameraView(background_image=bg))
    viz.set_layout(view)
    fake.json_messages.clear()

    bg.remove_layer(1)

    img_msgs = [
        m for m in fake.json_messages if m["type"] == "view_background_image"
    ]
    assert len(img_msgs) == 1
    meta = img_msgs[0]["image"]
    assert meta["images"][1] is None
    assert meta["uniforms"]["u_layer1_enabled"] == 0
    assert "img2" not in viz._layout._background_frames


def test_bound_remove_layer_zero_raises():  # noqa: ANN201
    from pytanga.viz import ImageView, Visualizer

    viz = Visualizer(add_default_axes=False, add_default_grid=False)
    fake = _FakeTransport()
    viz._layout._transport = fake  # type: ignore[attr-defined]

    bg = ImageView("bg")
    bg.set_image(ImageData("img1", data=np.zeros((8, 12, 3), dtype=np.uint8)))
    view = SceneView("main", camera_view=CameraView(background_image=bg))
    viz.set_layout(view)

    with pytest.raises(ValueError, match="layer 0"):
        bg.remove_layer(0)


def test_unbound_mutators_emit_nothing():  # noqa: ANN201
    from pytanga.viz import ImageView

    bg = ImageView("bg")
    bg.set_image(ImageData("img1", data=np.zeros((8, 12, 3), dtype=np.uint8)))
    bg.add_layer(ImageData("img2", data=np.zeros((8, 12), dtype=np.uint8)))
    # No transport bound: mutators change local state and never raise.
    bg.set_layer_style(1, ImageLayerStyle(opacity=0.3))
    bg.set_layer(1, ImageData("img3", data=np.ones((8, 12), dtype=np.uint8)))
    bg.set_uniform("u_brightness", 0.2)
    bg.remove_layer(1)
    assert bg.uniforms["u_layer1_enabled"] == 0

