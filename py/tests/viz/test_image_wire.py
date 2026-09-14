# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the binary image-frame codec (`_image_wire.py`)."""

from __future__ import annotations

import numpy as np
import pytest

from pytanga.viz._image_wire import _MAGIC, decode_image_frame, encode_image_frame
from pytanga.viz.image import ImageDType


@pytest.mark.parametrize(
    "dtype, shape, channels",
    [
        ("uint8", (3, 4), 1),
        ("uint16", (3, 4), 1),
        ("float32", (3, 4), 1),
        ("uint8", (3, 4, 3), 3),
        ("uint16", (3, 4, 4), 4),
        ("float32", (5, 2, 3), 3),
    ],
)
def test_round_trip(dtype: str, shape: tuple[int, ...], channels: int) -> None:
    arr = (np.arange(np.prod(shape), dtype=dtype) % 251).reshape(shape)
    decoded = decode_image_frame(encode_image_frame("img1", arr))
    assert decoded["id"] == "img1"
    assert decoded["width"] == shape[1]
    assert decoded["height"] == shape[0]
    assert decoded["channels"] == channels
    assert np.array_equal(decoded["data"], arr)


def test_header_dtype_code() -> None:
    frame = encode_image_frame("i", np.zeros((2, 2), dtype=np.uint16))
    decoded = decode_image_frame(frame)
    assert decoded["dtype"] is ImageDType.UINT16


def test_bad_magic() -> None:
    with pytest.raises(ValueError, match="magic"):
        decode_image_frame(b"XXXX" + b"\x00" * 40)


def test_too_short() -> None:
    with pytest.raises(ValueError, match="too short"):
        decode_image_frame(_MAGIC[:2])


def test_bad_version() -> None:
    frame = bytearray(encode_image_frame("i", np.zeros((2, 2), dtype=np.uint8)))
    frame[4] = 99  # version byte
    with pytest.raises(ValueError, match="version"):
        decode_image_frame(bytes(frame))


def test_bad_type() -> None:
    frame = bytearray(encode_image_frame("i", np.zeros((2, 2), dtype=np.uint8)))
    frame[5] = 99  # type byte
    with pytest.raises(ValueError, match="type"):
        decode_image_frame(bytes(frame))


def test_data_length_mismatch() -> None:
    frame = bytearray(encode_image_frame("i", np.zeros((2, 2), dtype=np.uint8)))
    frame = frame[:-1]  # drop one data byte
    with pytest.raises(ValueError, match="length mismatch"):
        decode_image_frame(bytes(frame))
