# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Binary WebSocket frame codec for image pixel data.

A frame is self-describing (id + dims + dtype in a fixed little-endian header)
so a binary image can be associated with its ``image`` entity without a separate
JSON "announce" message.  Pure data (no server/rendering imports), so it is
unit-testable and reusable by the export path.
"""

from __future__ import annotations

import struct
from typing import Any

import numpy as np

from .image import ImageDType

#: Frame magic — ``b"TGI\\0"``.
_MAGIC = b"TGI\x00"
_VERSION = 1
_TYPE_IMAGE = 1

# Header after the 4-byte magic (all little-endian):
#   version u8, type u8, id_len u8, width u32, height u32,
#   channels u8, dtype u8, data_len u64
_HEADER = struct.Struct("<BBBIIBBQ")


def encode_image_frame(image_id: str, data: np.ndarray) -> bytes:
    """Encode an image's pixel buffer into a binary frame.

    ``data`` must be a 2-D (H×W, 1 channel) or 3-D (H×W×C) array of a supported
    dtype.  Width/height/channels/dtype are derived from the array.
    """
    id_bytes = image_id.encode("ascii")
    if len(id_bytes) > 255:
        raise ValueError("image id must be at most 255 ASCII bytes")

    if data.ndim not in (2, 3):
        raise ValueError(f"expected a 2-D or 3-D array, got ndim={data.ndim}")

    arr = np.ascontiguousarray(data)
    dtype_code = ImageDType.from_numpy(arr).value
    channels = arr.shape[2] if arr.ndim == 3 else 1
    height, width = arr.shape[0], arr.shape[1]

    header = _HEADER.pack(
        _VERSION,
        _TYPE_IMAGE,
        len(id_bytes),
        width,
        height,
        channels,
        dtype_code,
        arr.nbytes,
    )
    return _MAGIC + header + id_bytes + arr.tobytes()


def decode_image_frame(buf: bytes) -> dict[str, Any]:
    """Decode a binary frame back into ``{id, width, height, channels, dtype, data}``."""
    if len(buf) < len(_MAGIC) + _HEADER.size:
        raise ValueError("image frame too short")
    if buf[: len(_MAGIC)] != _MAGIC:
        raise ValueError("bad image frame magic")

    version, ftype, id_len, width, height, channels, dtype_code, data_len = (
        _HEADER.unpack_from(buf, len(_MAGIC))
    )
    if version != _VERSION:
        raise ValueError(f"unsupported frame version {version}")
    if ftype != _TYPE_IMAGE:
        raise ValueError(f"unexpected frame type {ftype}")

    offset = len(_MAGIC) + _HEADER.size
    image_id = buf[offset : offset + id_len].decode("ascii")
    offset += id_len

    if len(buf) - offset != data_len:
        raise ValueError("image frame data length mismatch")

    dtype = ImageDType.from_code(dtype_code)
    arr = np.frombuffer(buf[offset:], dtype=dtype.numpy_dtype)
    if channels == 1:
        arr = arr.reshape((height, width))
    else:
        arr = arr.reshape((height, width, channels))

    return {
        "id": image_id,
        "width": width,
        "height": height,
        "channels": channels,
        "dtype": dtype,
        "data": arr,
    }
