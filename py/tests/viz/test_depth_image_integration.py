# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Integration tests for adding a `DepthImage` via `viz.add`/`viz.new`."""

from __future__ import annotations

from typing import Any

import numpy as np

from pytanga.viz import DepthImage, DepthImageData, DepthImageStyle, Visualizer
from pytanga.viz._nodes import VizDepthImage
from pytanga.viz._object_ref import VizObjectRef


class _FakeTransport:
    def __init__(self) -> None:
        self.messages: list[dict[str, Any]] = []
        self.bytes_sent: list[bytes] = []

    def send(self, message: dict[str, Any]) -> None:
        self.messages.append(message)

    def send_bytes(self, payload: bytes) -> None:
        self.bytes_sent.append(payload)


def _depth() -> DepthImage:
    return DepthImage(DepthImageData(depth=np.zeros((8, 8), np.float32)))


class TestAddDepthImage:
    def test_add_returns_id_and_node(self) -> None:
        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        handle = viz.scene("t")
        eid = handle.add(_depth())
        assert isinstance(eid, str)
        assert isinstance(handle.scene.get_node(eid), VizDepthImage)

    def test_new_returns_ref(self) -> None:
        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        handle = viz.scene("t")
        ref = handle.new(_depth(), style=DepthImageStyle(mesh_scale=0.5))
        assert isinstance(ref, VizObjectRef)
        assert isinstance(handle.scene.get_node(ref.id), VizDepthImage)


class TestDepthImageRefUniforms:
    def _setup(
        self,
    ) -> tuple[Visualizer, Any, VizObjectRef, VizDepthImage, _FakeTransport]:
        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        handle = viz.scene("t")
        fake = _FakeTransport()
        viz._transport = fake
        ref = handle.new(_depth())
        node = handle.scene.get_node(ref.id)
        assert isinstance(node, VizDepthImage)
        return viz, handle, ref, node, fake

    def test_set_uniform(self) -> None:
        _viz, _handle, ref, node, fake = self._setup()
        ref.set_uniform("u_angle", 0.5)
        assert node.payload["uniforms"]["u_angle"] == 0.5
        assert fake.messages[-1]["type"] == "depth_image_update"
        assert fake.messages[-1]["uniforms"] == {"u_angle": 0.5}

    def test_set_selected_segments(self) -> None:
        _viz, _handle, ref, node, fake = self._setup()
        ref.set_selected_segments([1, 2])
        assert node.payload["uniforms"]["u_seg_enabled"] == 1
        assert node.payload["uniforms"]["u_num_selected"] == 2
        last = fake.messages[-1]
        assert last["type"] == "depth_image_update"
        assert last["uniforms"]["u_num_selected"] == 2

    def test_set_selected_segments_empty_disables(self) -> None:
        _viz, _handle, ref, node, _fake = self._setup()
        ref.set_selected_segments([])
        assert node.payload["uniforms"]["u_seg_enabled"] == 0
        assert node.payload["uniforms"]["u_num_selected"] == 0

    def test_frames_pushed_on_add(self) -> None:
        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        handle = viz.scene("t")
        fake = _FakeTransport()
        viz._transport = fake
        handle.add(_depth())
        assert len(fake.bytes_sent) == 1
