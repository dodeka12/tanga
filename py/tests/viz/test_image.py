# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the image value types and PIL bridge (`image.py`)."""

from __future__ import annotations

import sys

import numpy as np
import pytest

from pytanga.viz.image import (
    ImageChannelMode,
    ImageData,
    ImageDType,
    default_mode,
    default_value_range,
    pil_to_numpy,
)


class TestImageDType:
    @pytest.mark.parametrize(
        "code, expected",
        [(0, ImageDType.UINT8), (1, ImageDType.UINT16), (2, ImageDType.FLOAT32)],
    )
    def test_from_code(self, code: int, expected: ImageDType) -> None:
        assert ImageDType.from_code(code) is expected

    def test_from_code_unknown(self) -> None:
        with pytest.raises(ValueError, match="Unknown image dtype code"):
            ImageDType.from_code(9)

    def test_numpy_dtype(self) -> None:
        assert ImageDType.UINT8.numpy_dtype == np.dtype("uint8")
        assert ImageDType.UINT16.numpy_dtype == np.dtype("uint16")
        assert ImageDType.FLOAT32.numpy_dtype == np.dtype("float32")

    def test_internal_format(self) -> None:
        assert ImageDType.UINT8.to_internal_format() == "uint8"
        assert ImageDType.UINT16.to_internal_format() == "uint16"
        assert ImageDType.FLOAT32.to_internal_format() == "float32"

    def test_from_numpy(self) -> None:
        assert (
            ImageDType.from_numpy(np.zeros((2, 2), dtype=np.uint16))
            is ImageDType.UINT16
        )
        assert (
            ImageDType.from_numpy(np.zeros((2, 2), dtype=np.float32))
            is ImageDType.FLOAT32
        )

    def test_from_numpy_unsupported(self) -> None:
        with pytest.raises(ValueError, match="Unsupported numpy dtype"):
            ImageDType.from_numpy(np.zeros((2, 2), dtype=np.int16))


class TestHelpers:
    @pytest.mark.parametrize(
        "channels, expected",
        [
            (1, ImageChannelMode.GRAY),
            (3, ImageChannelMode.RGB),
            (4, ImageChannelMode.RGB),
        ],
    )
    def test_default_mode(self, channels: int, expected: ImageChannelMode) -> None:
        assert default_mode(channels) == int(expected)

    def test_default_value_range(self) -> None:
        assert default_value_range(ImageDType.UINT8) == (0.0, 1.0)
        assert default_value_range(ImageDType.FLOAT32) == (0.0, 1.0)
        assert default_value_range(ImageDType.UINT16) == (0.0, 65535.0)


class TestImageData:
    def test_derives_metadata_from_data(self) -> None:
        img = ImageData("i", data=np.zeros((3, 4), dtype=np.uint8))
        assert (img.width, img.height, img.channels) == (4, 3, 1)
        assert img.dtype is ImageDType.UINT8

    def test_3d_rgb(self) -> None:
        img = ImageData("i", data=np.zeros((3, 4, 3), dtype=np.uint8))
        assert (img.width, img.height, img.channels) == (4, 3, 3)

    def test_requires_exactly_one_of_data_or_url(self) -> None:
        with pytest.raises(ValueError, match="exactly one"):
            ImageData("i")
        with pytest.raises(ValueError, match="exactly one"):
            ImageData("i", data=np.zeros((2, 2), dtype=np.uint8), url="http://x")

    def test_url_requires_metadata(self) -> None:
        with pytest.raises(ValueError, match="required"):
            ImageData("u", url="http://x")
        img = ImageData(
            "u", url="http://x", width=4, height=3, channels=3, dtype=ImageDType.UINT8
        )
        assert img.source == "url"

    def test_bad_channels(self) -> None:
        with pytest.raises(ValueError, match="1, 3, or 4 channels"):
            ImageData("i", data=np.zeros((2, 2, 5), dtype=np.uint8))

    def test_bad_ndim(self) -> None:
        with pytest.raises(ValueError, match="2-D"):
            ImageData("i", data=np.zeros((2, 2, 2, 2), dtype=np.uint8))

    def test_dtype_mismatch(self) -> None:
        with pytest.raises(ValueError, match="does not match"):
            ImageData(
                "i", data=np.zeros((2, 2), dtype=np.uint8), dtype=ImageDType.UINT16
            )

    def test_width_mismatch(self) -> None:
        with pytest.raises(ValueError, match="does not match"):
            ImageData("i", data=np.zeros((2, 2), dtype=np.uint8), width=99)

    def test_non_contiguous_becomes_contiguous(self) -> None:
        src = np.zeros((4, 6, 3), dtype=np.uint8)[:, ::2]
        assert not src.flags["C_CONTIGUOUS"]
        img = ImageData("i", data=src)
        assert img.data is not None
        assert img.data.flags["C_CONTIGUOUS"]

    def test_auto_tiles_large_by_dim(self) -> None:
        img = ImageData("i", data=np.zeros((5000, 100, 3), dtype=np.uint8))
        assert img.source == "tiled"
        assert img.data is None
        assert img.tiled is not None
        assert (img.width, img.height, img.channels) == (100, 5000, 3)

    def test_auto_tiles_large_by_bytes(self) -> None:
        # 4096 × 4096 × 3 bytes ≈ 48 MB, over the 32 MB default threshold.
        img = ImageData("i", data=np.zeros((4096, 4096, 3), dtype=np.uint8))
        assert img.source == "tiled"

    def test_does_not_tile_small(self) -> None:
        img = ImageData("i", data=np.zeros((512, 512, 3), dtype=np.uint8))
        assert img.source == "data"
        assert img.data is not None

    def test_auto_tile_opt_out(self) -> None:
        img = ImageData(
            "i",
            data=np.zeros((5000, 100, 3), dtype=np.uint8),
            tile_max_dim=None,
            tile_max_bytes=None,
        )
        assert img.source == "data"
        assert img.data is not None

    def test_to_bytes_and_base64(self) -> None:
        import base64

        arr = np.arange(6, dtype=np.uint8).reshape(2, 3)
        img = ImageData("i", data=arr)
        assert img.to_bytes() == arr.tobytes()
        assert img.to_base64() == base64.b64encode(arr.tobytes()).decode("ascii")

    def test_to_bytes_url_raises(self) -> None:
        img = ImageData(
            "u", url="http://x", width=4, height=3, channels=3, dtype=ImageDType.UINT8
        )
        with pytest.raises(ValueError, match="no pixel buffer"):
            img.to_bytes()


class TestPilToNumpy:
    def test_missing_pil_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setitem(sys.modules, "PIL", None)
        with pytest.raises(ImportError, match="Pillow"):
            pil_to_numpy(object())

    def test_l_grayscale(self) -> None:
        from PIL import Image

        arr = pil_to_numpy(Image.new("L", (4, 3), 128))
        assert arr.shape == (3, 4)
        assert arr.dtype == np.uint8

    def test_rgb(self) -> None:
        from PIL import Image

        arr = pil_to_numpy(Image.new("RGB", (4, 3)))
        assert arr.shape == (3, 4, 3)
        assert arr.dtype == np.uint8

    def test_rgba(self) -> None:
        from PIL import Image

        arr = pil_to_numpy(Image.new("RGBA", (4, 3)))
        assert arr.shape == (3, 4, 4)
        assert arr.dtype == np.uint8

    def test_i16(self) -> None:
        from PIL import Image

        arr = pil_to_numpy(Image.new("I;16", (4, 3)))
        assert arr.shape == (3, 4)
        assert arr.dtype == np.uint16

    def test_f(self) -> None:
        from PIL import Image

        arr = pil_to_numpy(Image.new("F", (4, 3)))
        assert arr.shape == (3, 4)
        assert arr.dtype == np.float32

    def test_target_dtype_conversion(self) -> None:
        from PIL import Image

        arr = pil_to_numpy(Image.new("RGB", (4, 3)), dtype="float32")
        assert arr.dtype == np.float32
        assert arr.shape == (3, 4, 3)

    def test_unsupported_dtype(self) -> None:
        from PIL import Image

        with pytest.raises(ValueError, match="Unsupported target dtype"):
            pil_to_numpy(Image.new("L", (4, 3)), dtype="int64")
