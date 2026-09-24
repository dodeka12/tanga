# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for image codec selection and the v2 wire format (`_image_wire.py`)."""

from __future__ import annotations

import sys

import numpy as np
import pytest

from pytanga.viz._image_wire import (
    _MAGIC,
    _V1_HEADER,
    decode_image_frame,
    encode_image_frame,
)
from pytanga.viz.image import EImageCodec, ImageDType


def _frame_codec(frame: bytes) -> int:
    """Read the codec byte from a v2 frame (magic 4 + version/type/id_len)."""
    return frame[7]


@pytest.mark.parametrize(
    "codec, code",
    [
        (EImageCodec.RAW, EImageCodec.RAW.value),
        (EImageCodec.JPEG, EImageCodec.JPEG.value),
        (EImageCodec.ZLIB, EImageCodec.ZLIB.value),
    ],
)
def test_codec_byte(codec: EImageCodec, code: int) -> None:
    frame = encode_image_frame("i", np.zeros((2, 2, 3), dtype=np.uint8), codec=codec)
    assert _frame_codec(frame) == code


def test_auto_selects_jpeg_for_uint8_rgb() -> None:
    frame = encode_image_frame("i", np.zeros((2, 2, 3), dtype=np.uint8))
    assert _frame_codec(frame) == EImageCodec.JPEG.value


def test_auto_selects_jpeg_for_uint8_gray() -> None:
    frame = encode_image_frame("i", np.zeros((2, 2), dtype=np.uint8))
    assert _frame_codec(frame) == EImageCodec.JPEG.value


@pytest.mark.parametrize(
    "dtype, shape",
    [("uint16", (2, 2)), ("float32", (2, 2)), ("uint8", (2, 2, 4))],
)
def test_auto_selects_zlib_when_jpeg_unsuitable(dtype: str, shape: tuple[int, ...]) -> None:
    frame = encode_image_frame("i", np.zeros(shape, dtype=dtype))
    assert _frame_codec(frame) == EImageCodec.ZLIB.value


@pytest.mark.parametrize(
    "dtype, shape",
    [("uint16", (3, 4)), ("float32", (3, 4, 3))],
)
def test_zlib_round_trip_is_lossless(dtype: str, shape: tuple[int, ...]) -> None:
    arr = (np.arange(np.prod(shape), dtype=dtype) % 251).reshape(shape)
    decoded = decode_image_frame(encode_image_frame("img1", arr, codec=EImageCodec.ZLIB))
    assert decoded["id"] == "img1"
    assert decoded["codec"] is EImageCodec.ZLIB
    assert decoded["width"] == shape[1]
    assert decoded["height"] == shape[0]
    assert np.array_equal(decoded["data"], arr)


def test_jpeg_round_trip_recovers_dims_and_dtype() -> None:
    arr = np.arange(3 * 4 * 3, dtype=np.uint8).reshape(3, 4, 3)
    decoded = decode_image_frame(encode_image_frame("img1", arr, codec=EImageCodec.JPEG))
    assert decoded["id"] == "img1"
    assert decoded["codec"] is EImageCodec.JPEG
    assert decoded["width"] == 4
    assert decoded["height"] == 3
    assert decoded["channels"] == 3
    assert decoded["dtype"] is ImageDType.UINT8
    assert decoded["data"].shape == (3, 4, 3)


def test_jpeg_missing_pillow_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "PIL", None)
    with pytest.raises(ImportError, match="Pillow"):
        encode_image_frame("i", np.zeros((2, 2, 3), dtype=np.uint8), codec=EImageCodec.JPEG)


def test_v1_frame_still_decodes() -> None:
    arr = np.arange(6, dtype=np.uint8).reshape(2, 3)
    id_bytes = b"img1"
    header = _V1_HEADER.pack(
        1, 1, len(id_bytes), arr.shape[1], arr.shape[0], 1, ImageDType.UINT8.value, arr.nbytes
    )
    frame = _MAGIC + header + id_bytes + arr.tobytes()
    decoded = decode_image_frame(frame)
    assert decoded["codec"] is EImageCodec.RAW
    assert np.array_equal(decoded["data"], arr)
