# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Binary WebSocket frame codec for image pixel data.

A frame is self-describing (id + dims + dtype in a fixed little-endian header)
so a binary image can be associated with its ``image`` entity without a separate
JSON "announce" message.  Pure data (no server/rendering imports), so it is
unit-testable and reusable by the export path.
"""

from __future__ import annotations

import io
import struct
import zlib
from dataclasses import dataclass
from typing import Any

import numpy as np

from .image import EImageCodec, ImageDType

#: Frame magic — ``b"TGI\\0"``.
_MAGIC = b"TGI\x00"
_VERSION = 2
_TYPE_IMAGE = 1

# v1 header (no codec byte) is still accepted on decode.
_V1_HEADER = struct.Struct("<BBBIIBBQ")
# v2 header: version u8, type u8, id_len u8, codec u8, width u32, height u32,
#   channels u8, dtype u8, data_len u64
_HEADER = struct.Struct("<BBBBIIBBQ")

def encode_jpeg(data: np.ndarray, quality: int = 85) -> bytes:
    """Encode a ``uint8`` H×W or H×W×3 array as JPEG bytes (lazy Pillow)."""
    try:
        from PIL import Image
    except ImportError as exc:
        raise ImportError(
            "JPEG encoding requires Pillow; install it (e.g. `pip install pillow`) "
            "or use codec='raw'/'zlib'"
        ) from exc
    if data.dtype != np.dtype("uint8"):
        raise ValueError(f"JPEG requires uint8 data, got dtype={data.dtype!r}")
    if data.ndim == 2:
        mode = "L"
    elif data.ndim == 3 and data.shape[2] == 3:
        mode = "RGB"
    else:
        raise ValueError(
            f"JPEG requires 1 or 3 channels, got ndim={data.ndim}, shape={data.shape}"
        )
    image = Image.fromarray(np.ascontiguousarray(data), mode=mode)
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=quality)
    return buffer.getvalue()


def encode_zlib_raw(data: np.ndarray) -> bytes:
    """Losslessly encode the raw pixel buffer with zlib (stdlib)."""
    return zlib.compress(np.ascontiguousarray(data).tobytes())


def _resolve_codec(arr: np.ndarray, codec: EImageCodec | None) -> EImageCodec:
    if codec is None:
        channels = arr.shape[2] if arr.ndim == 3 else 1
        if ImageDType.from_numpy(arr) is ImageDType.UINT8 and channels in (1, 3):
            return EImageCodec.JPEG
        return EImageCodec.ZLIB
    return codec


def _encode_payload(arr: np.ndarray, codec: EImageCodec, jpeg_quality: int) -> bytes:
    if codec is EImageCodec.RAW:
        return arr.tobytes()
    if codec is EImageCodec.ZLIB:
        return encode_zlib_raw(arr)
    return encode_jpeg(arr, jpeg_quality)


def encode_image_frame(
    image_id: str,
    data: np.ndarray,
    *,
    codec: EImageCodec | None = None,
    jpeg_quality: int = 85,
) -> bytes:
    """Encode an image's pixel buffer into a binary frame.

    ``data`` must be a 2-D (H×W, 1 channel) or 3-D (H×W×C) array of a supported
    dtype.  *codec* selects the wire codec; ``None`` (the default) auto-selects
    JPEG for 8-bit 1/3-channel data and lossless zlib otherwise.
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
    codec_enum = _resolve_codec(arr, codec)
    payload = _encode_payload(arr, codec_enum, jpeg_quality)

    header = _HEADER.pack(
        _VERSION,
        _TYPE_IMAGE,
        len(id_bytes),
        codec_enum.value,
        width,
        height,
        channels,
        dtype_code,
        len(payload),
    )
    return _MAGIC + header + id_bytes + payload


def _decode_pixels(payload: bytes, codec: EImageCodec, dtype: ImageDType) -> np.ndarray:
    if codec is EImageCodec.RAW:
        return np.frombuffer(payload, dtype=dtype.numpy_dtype)
    if codec is EImageCodec.ZLIB:
        return np.frombuffer(zlib.decompress(payload), dtype=dtype.numpy_dtype)
    # JPEG
    try:
        from PIL import Image
    except ImportError as exc:
        raise ImportError(
            "JPEG decoding requires Pillow; install it (e.g. `pip install pillow`)"
        ) from exc
    return np.asarray(Image.open(io.BytesIO(payload)))


@dataclass(frozen=True, slots=True)
class ImageFrameHeader:
    """Decoded binary-frame header fields (magic excluded).

    ``codec`` and ``dtype`` are resolved to their enum types during parsing;
    the remaining fields are the raw little-endian values from the wire.
    """

    version: int
    ftype: int
    id_len: int
    codec: EImageCodec
    width: int
    height: int
    channels: int
    dtype: ImageDType
    data_len: int


def _decode_header(buf: bytes) -> tuple[ImageFrameHeader, int]:
    """Parse magic + header; return ``(header, payload_offset)``.

    ``payload_offset`` is the byte index where the image id begins (just past
    the header).
    """
    if len(buf) < len(_MAGIC):
        raise ValueError("image frame too short")
    if buf[: len(_MAGIC)] != _MAGIC:
        raise ValueError("bad image frame magic")
    if len(buf) < len(_MAGIC) + 1:
        raise ValueError("image frame too short")

    version = buf[len(_MAGIC)]
    if version == 1:
        struct_ = _V1_HEADER
    elif version == 2:
        struct_ = _HEADER
    else:
        raise ValueError(f"unsupported frame version {version}")

    if len(buf) < len(_MAGIC) + struct_.size:
        raise ValueError("image frame too short")

    fields = struct_.unpack_from(buf, len(_MAGIC))
    if version == 1:
        _, ftype, id_len, width, height, channels, dtype_code, data_len = fields
        codec = EImageCodec.RAW
    else:
        _, ftype, id_len, codec_code, width, height, channels, dtype_code, data_len = fields
        codec = EImageCodec.from_code(codec_code)

    header = ImageFrameHeader(
        version=version,
        ftype=ftype,
        id_len=id_len,
        codec=codec,
        width=width,
        height=height,
        channels=channels,
        dtype=ImageDType.from_code(dtype_code),
        data_len=data_len,
    )
    return header, len(_MAGIC) + struct_.size


def decode_image_frame(buf: bytes) -> dict[str, Any]:
    """Decode a binary frame into ``{id, width, height, channels, dtype, codec, data}``.

    Accepts v1 (codec implied ``raw``) and v2 frames.
    """
    header, offset = _decode_header(buf)
    if header.ftype != _TYPE_IMAGE:
        raise ValueError(f"unexpected frame type {header.ftype}")

    image_id = buf[offset : offset + header.id_len].decode("ascii")
    offset += header.id_len

    if len(buf) - offset != header.data_len:
        raise ValueError("image frame data length mismatch")

    arr = _decode_pixels(buf[offset:], header.codec, header.dtype)
    if header.channels == 1:
        arr = arr.reshape((header.height, header.width))
    else:
        arr = arr.reshape((header.height, header.width, header.channels))

    return {
        "id": image_id,
        "width": header.width,
        "height": header.height,
        "channels": header.channels,
        "dtype": header.dtype,
        "codec": header.codec,
        "data": arr,
    }
