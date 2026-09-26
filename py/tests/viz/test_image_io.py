# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the dependency-free image readers (`_image_io.py`)."""

from __future__ import annotations

import struct
import zlib
from pathlib import Path
from types import ModuleType

import numpy as np
import pytest

from pytanga.viz import _image_io
from pytanga.viz._image_io import _reorder_exr_pixels
from pytanga.viz.image import read_exr, read_hdr, register_loading_progress_handler

_HEADER = b"#?RADIANCE\nFORMAT=32-bit_rle_rgbe"


def _hdr(resolution: bytes, pixels: bytes) -> bytes:
    return _HEADER + b"\n\n" + resolution + b"\n" + pixels


def _dec(r: int, g: int, b: int, e: int) -> np.ndarray:
    """Decode one RGBE quad to its exact float32 RGB (the spec formula)."""
    scale = 0.0 if e == 0 else 2.0 ** (e - 136)
    return np.array(
        [(r + 0.5) * scale, (g + 0.5) * scale, (b + 0.5) * scale], dtype=np.float32
    )


_RED = bytes([255, 0, 0, 128])
_GREEN = bytes([0, 255, 0, 128])
_BLUE = bytes([0, 0, 255, 128])
_GRAY = bytes([128, 128, 128, 128])
_BRIGHT = bytes([255, 0, 0, 130])
_BLACK = bytes([0, 0, 0, 0])
_DEEP_BLUE = bytes([0, 0, 255, 136])

_RED_F = _dec(255, 0, 0, 128)
_GREEN_F = _dec(0, 255, 0, 128)
_BLUE_F = _dec(0, 0, 255, 128)
_GRAY_F = _dec(128, 128, 128, 128)
_BRIGHT_F = _dec(255, 0, 0, 130)
_BLACK_F = _dec(0, 0, 0, 0)
_DEEP_BLUE_F = _dec(0, 0, 255, 136)


def test_read_hdr_flat() -> None:
    data = _hdr(b"-Y 2 +X 2", _RED + _BRIGHT + _BLACK + _DEEP_BLUE)
    img = read_hdr(data)
    assert img.dtype == np.float32
    assert img.shape == (2, 2, 3)
    assert np.allclose(img[0, 0], _RED_F)
    assert np.allclose(img[0, 1], _BRIGHT_F)
    assert np.allclose(img[1, 0], _BLACK_F)
    assert np.allclose(img[1, 1], _DEEP_BLUE_F)


def test_read_hdr_new_rle() -> None:
    # Row 0: (128,128,128,128), (255,0,0,130); row 1: (0,0,0,0), (0,0,255,136).
    # Component streams interleave R,G,B,E; count > 128 is a run, else literal.
    row0 = bytes([2, 2, 0, 2]) + bytes([2, 128, 255, 2, 128, 0, 2, 128, 0, 2, 128, 130])
    row1 = bytes([2, 2, 0, 2]) + bytes([130, 0, 130, 0, 2, 0, 255, 2, 0, 136])
    img = read_hdr(_hdr(b"-Y 2 +X 2", row0 + row1))
    assert img.shape == (2, 2, 3)
    assert np.allclose(img[0, 0], _GRAY_F)
    assert np.allclose(img[0, 1], _BRIGHT_F)
    assert np.allclose(img[1, 0], _BLACK_F)
    assert np.allclose(img[1, 1], _DEEP_BLUE_F)


def test_read_hdr_flip_y() -> None:
    # +Y: file rows are bottom -> top, so read_hdr must flip vertically.
    data = _hdr(b"+Y 2 +X 2", _BLUE + _GRAY + _RED + _GREEN)
    img = read_hdr(data)
    assert np.allclose(img[0, 0], _RED_F)
    assert np.allclose(img[0, 1], _GREEN_F)
    assert np.allclose(img[1, 0], _BLUE_F)
    assert np.allclose(img[1, 1], _GRAY_F)


def test_read_hdr_flip_x() -> None:
    # -X: each row is right -> left, so read_hdr must flip horizontally.
    data = _hdr(b"-Y 2 -X 2", _GREEN + _RED + _GRAY + _BLUE)
    img = read_hdr(data)
    assert np.allclose(img[0, 0], _RED_F)
    assert np.allclose(img[0, 1], _GREEN_F)
    assert np.allclose(img[1, 0], _BLUE_F)
    assert np.allclose(img[1, 1], _GRAY_F)


def test_read_hdr_from_path(tmp_path: Path) -> None:
    path = tmp_path / "test.hdr"
    path.write_bytes(_hdr(b"-Y 1 +X 1", _RED))
    assert np.allclose(read_hdr(path)[0, 0], _RED_F)


def test_read_hdr_rejects_bad_magic() -> None:
    with pytest.raises(ValueError, match="bad magic"):
        read_hdr(b"not a hdr file\n\n-Y 1 +X 1\n" + _RED)


def test_read_hdr_rejects_missing_resolution() -> None:
    with pytest.raises(ValueError, match="resolution"):
        read_hdr(_HEADER + b"\n\n")


def test_read_hdr_rejects_truncated_rle() -> None:
    with pytest.raises(ValueError, match="truncated"):
        read_hdr(_hdr(b"-Y 1 +X 2", bytes([2, 2, 0, 2, 130])))


# --------------------------------------------------------------------------
# OpenEXR (`.exr`)
# --------------------------------------------------------------------------

_EXR_MAGIC = 20000630
_EXR_DTYPE = {0: np.uint32, 1: np.float16, 2: np.float32}


def _exr_attr(name: str, atype: str, value: bytes) -> bytes:
    return (
        name.encode()
        + b"\0"
        + atype.encode()
        + b"\0"
        + struct.pack("<i", len(value))
        + value
    )


def _exr_none(
    pixels: np.ndarray,
    *,
    pixel_type: int = 1,
    channels: tuple[str, ...] = ("R", "G", "B"),
    compression: int = 0,
    version: int = 2,
) -> bytes:
    """Build a scanline OpenEXR with NONE compression around a float pixel array."""
    h, w, c = pixels.shape
    dtype = _EXR_DTYPE[pixel_type]
    arr = np.ascontiguousarray(pixels, dtype=dtype)

    chlist = b""
    for name in channels:
        chlist += name.encode() + b"\0"
        chlist += struct.pack("<i", pixel_type)
        chlist += b"\0" * 4  # pLinear + reserved
        chlist += struct.pack("<i", 1) + struct.pack("<i", 1)
    chlist += b"\0"

    header = b""
    header += _exr_attr("channels", "chlist", chlist)
    header += _exr_attr("compression", "compression", struct.pack("<B", compression))
    header += _exr_attr("dataWindow", "box2i", struct.pack("<4i", 0, 0, w - 1, h - 1))
    header += _exr_attr("lineOrder", "lineOrder", struct.pack("<B", 0))
    header += b"\0"

    magic = struct.pack("<I", _EXR_MAGIC)
    ver = struct.pack("<I", version)

    # NONE: one scanline per chunk.
    chunks = []
    for y in range(h):
        line = arr[y].tobytes()
        chunks.append(struct.pack("<ii", y, len(line)) + line)

    table_pos = len(magic) + len(ver) + len(header)
    chunk_start = table_pos + 8 * len(chunks)
    offset = chunk_start
    offsets: list[int] = []
    for chunk in chunks:
        offsets.append(offset)
        offset += len(chunk)

    out = magic + ver + header
    out += b"".join(struct.pack("<q", o) for o in offsets)
    out += b"".join(chunks)
    return out


def _rle_encode(data: bytes) -> bytes:
    """Encode *data* with the OpenEXR RLE scheme (test fixture generator)."""
    out = bytearray()
    i, n = 0, len(data)
    while i < n:
        j = i
        while j < n and data[j] == data[i] and j - i < 128:
            j += 1
        if j - i >= 3:
            out.append(256 - (j - i))
            out.append(data[i])
        else:
            out.append(0)
            out.append(data[i])
        i = j
    return bytes(out)


def _exr_scanline(
    pixels: np.ndarray,
    *,
    compression: int,
    pixel_type: int = 1,
    channels: tuple[str, ...] = ("R", "G", "B"),
) -> bytes:
    """Build an RLE/ZIPS/ZIP OpenEXR around a float pixel array."""
    h, w, _c = pixels.shape
    arr = np.ascontiguousarray(pixels, dtype=_EXR_DTYPE[pixel_type])
    sample_bytes = {0: 4, 1: 2, 2: 4}[pixel_type]
    bytes_per_pixel = sample_bytes * len(channels)
    lines_per_chunk = {1: 1, 2: 1, 3: 16}[compression]

    chlist = b""
    for name in channels:
        chlist += name.encode() + b"\0"
        chlist += struct.pack("<i", pixel_type)
        chlist += b"\0" * 4
        chlist += struct.pack("<i", 1) + struct.pack("<i", 1)
    chlist += b"\0"

    header = b""
    header += _exr_attr("channels", "chlist", chlist)
    header += _exr_attr("compression", "compression", struct.pack("<B", compression))
    header += _exr_attr("dataWindow", "box2i", struct.pack("<4i", 0, 0, w - 1, h - 1))
    header += _exr_attr("lineOrder", "lineOrder", struct.pack("<B", 0))
    header += b"\0"

    magic = struct.pack("<I", _EXR_MAGIC)
    ver = struct.pack("<I", 2)

    chunks = []
    n_chunks = (h + lines_per_chunk - 1) // lines_per_chunk
    for ci in range(n_chunks):
        y0 = ci * lines_per_chunk
        n_lines = min(lines_per_chunk, h - y0)
        raw = arr[y0 : y0 + n_lines].tobytes()
        if compression == 1:
            data = _rle_encode(raw)
        else:  # ZIPS / ZIP
            reordered = _reorder_exr_pixels(raw, bytes_per_pixel)
            data = struct.pack("<H", len(reordered)) + zlib.compress(reordered)
        chunks.append(struct.pack("<ii", y0, len(data)) + data)

    table_pos = len(magic) + len(ver) + len(header)
    chunk_start = table_pos + 8 * len(chunks)
    offset = chunk_start
    offsets: list[int] = []
    for chunk in chunks:
        offsets.append(offset)
        offset += len(chunk)

    out = magic + ver + header
    out += b"".join(struct.pack("<q", o) for o in offsets)
    out += b"".join(chunks)
    return out


_PIXELS = np.array(
    [
        [[1.0, 0.5, 0.25], [2.0, 1.0, 0.5]],
        [[0.5, 0.5, 0.5], [0.5, 0.5, 0.5]],
    ],
    dtype=np.float64,
)


def test_read_exr_rle() -> None:
    assert np.allclose(read_exr(_exr_scanline(_PIXELS, compression=1)), _PIXELS)


def test_read_exr_zips() -> None:
    assert np.allclose(read_exr(_exr_scanline(_PIXELS, compression=2)), _PIXELS)


def test_read_exr_zip() -> None:
    assert np.allclose(read_exr(_exr_scanline(_PIXELS, compression=3)), _PIXELS)


def test_exr_reorder_pixels() -> None:
    assert (
        _reorder_exr_pixels(b"\x00\x01\x02\x03\x04\x05", 6)
        == b"\x03\x04\x05\x00\x01\x02"
    )


def test_read_exr_none_half() -> None:
    pixels = np.array(
        [
            [[1.0, 0.5, 0.25], [0.0, 0.0, 0.0]],
            [[2.0, 1.0, 0.5], [0.5, 0.5, 0.5]],
        ],
        dtype=np.float64,
    )
    img = read_exr(_exr_none(pixels, pixel_type=1))
    assert img.dtype == np.float32
    assert img.shape == (2, 2, 3)
    assert np.allclose(img, pixels.astype(np.float32))


def test_read_exr_none_float() -> None:
    pixels = np.array([[[0.1, 0.2, 0.3], [1.5, 2.5, 3.5]]], dtype=np.float32)
    img = read_exr(_exr_none(pixels, pixel_type=2))
    assert np.array_equal(img, pixels)


def test_read_exr_none_uint() -> None:
    pixels = np.array([[[0, 1000, 65535], [4294967295, 1, 2]]], dtype=np.uint32)
    img = read_exr(_exr_none(pixels.astype(np.float64), pixel_type=0))
    assert np.array_equal(img, pixels.astype(np.float32))


def test_read_exr_rejects_bad_magic() -> None:
    with pytest.raises(ValueError, match="bad magic"):
        read_exr(struct.pack("<2I", 0, 2))


def test_read_exr_rejects_tiled() -> None:
    with pytest.raises(ValueError, match="tiled"):
        read_exr(struct.pack("<2I", _EXR_MAGIC, 2 | 0x200))


def test_read_exr_rejects_unsupported_compression() -> None:
    pixels = np.zeros((1, 1, 3), dtype=np.float64)
    with pytest.raises(ValueError, match="unsupported OpenEXR compression"):
        read_exr(_exr_none(pixels, compression=10))


def test_read_exr_piz() -> None:
    # Reference file written by the OpenEXR library (PIZ, RGB half).
    path = Path(__file__).parent / "data" / "piz_rgb.exr"
    img = read_exr(path)
    w = h = 16
    xs = np.arange(w, dtype=np.float32) / 15.0
    ys = np.arange(h, dtype=np.float32) / 15.0
    r = np.tile(xs.astype(np.float16).astype(np.float32), (h, 1))
    g = np.tile(ys.astype(np.float16).astype(np.float32)[:, None], (1, w))
    b = np.full((h, w), 0.5, dtype=np.float32)
    expected = np.stack([r, g, b], axis=-1)
    assert img.shape == (h, w, 3)
    assert img.dtype == np.float32
    assert np.array_equal(img, expected)


def _exr_piz_raw(pixels: np.ndarray) -> bytes:
    """Build a PIZ file whose chunk is the raw channel-planar-per-scanline data."""
    h, w, _c = pixels.shape
    arr = np.ascontiguousarray(pixels, dtype=np.float16)
    raw = b"".join(arr[y, :, c].tobytes() for y in range(h) for c in range(3))

    chlist = b""
    for name in ("R", "G", "B"):
        chlist += name.encode() + b"\0" + struct.pack("<i", 1) + b"\0" * 4
        chlist += struct.pack("<i", 1) + struct.pack("<i", 1)
    chlist += b"\0"

    header = b""
    header += _exr_attr("channels", "chlist", chlist)
    header += _exr_attr("compression", "compression", struct.pack("<B", 4))
    header += _exr_attr("dataWindow", "box2i", struct.pack("<4i", 0, 0, w - 1, h - 1))
    header += _exr_attr("lineOrder", "lineOrder", struct.pack("<B", 0))
    header += b"\0"

    magic = struct.pack("<I", _EXR_MAGIC)
    ver = struct.pack("<I", 2)
    chunk = struct.pack("<ii", 0, len(raw)) + raw
    offset = len(magic) + len(ver) + len(header) + 8
    return magic + ver + header + struct.pack("<q", offset) + chunk


def test_read_exr_piz_raw_fallback() -> None:
    pixels = np.array(
        [
            [[1.0, 0.5, 0.25], [2.0, 1.0, 0.5]],
            [[0.5, 0.5, 0.5], [0.25, 0.5, 0.75]],
        ],
        dtype=np.float64,
    )
    img = read_exr(_exr_piz_raw(pixels))
    assert img.shape == (2, 2, 3)
    assert np.allclose(img, pixels.astype(np.float32))


def _piz_binding_or_none() -> ModuleType | None:
    """Load ``binding_piz`` if a compiler/precompiled binary is available."""
    try:
        from pytanga.codegen._piz_cache import get_or_build_piz

        return get_or_build_piz()
    except Exception:
        return None


def _piz_reference_chunk() -> tuple[bytes, list[tuple[str, int, int, int]], int, int]:
    """Return ``(chunk, channels, width, n_lines)`` for the committed piz_rgb.exr."""
    data = (Path(__file__).parent / "data" / "piz_rgb.exr").read_bytes()
    header, offset = _image_io._parse_exr_header(data, 8)
    channels = _image_io._parse_exr_channels(header["channels"])
    compression = header["compression"][0]
    min_x, min_y, max_x, max_y = struct.unpack("<4i", header["dataWindow"])
    width = max_x - min_x + 1
    height = max_y - min_y + 1
    lines_per_chunk = _image_io._EXR_LINES_PER_CHUNK[compression]
    n_chunks = (height + lines_per_chunk - 1) // lines_per_chunk
    offsets = struct.unpack_from(f"<{n_chunks}q", data, offset)
    y, size = struct.unpack_from("<2i", data, offsets[0])
    chunk = data[offsets[0] + 8 : offsets[0] + 8 + size]
    n_lines = min(lines_per_chunk, height - (y - min_y))
    return chunk, channels, width, n_lines


def test_piz_binding_matches_numpy() -> None:
    binding = _piz_binding_or_none()
    if binding is None:
        pytest.skip("binding_piz unavailable (no compiler/precompiled binary)")
    chunk, channels, width, n_lines = _piz_reference_chunk()
    sizes = [1 if pt == 1 else 2 for _name, pt, _x, _y in channels]
    expected = _image_io._decode_exr_piz(chunk, channels, width, n_lines)
    assert binding.piz_decode(chunk, width, n_lines, sizes) == expected


def test_piz_binding_raw_fallback_matches_numpy() -> None:
    binding = _piz_binding_or_none()
    if binding is None:
        pytest.skip("binding_piz unavailable (no compiler/precompiled binary)")
    h, w = 3, 5
    pixels = np.arange(h * w * 3, dtype=np.uint16).reshape(h, w, 3)
    raw = b"".join(pixels[y, :, c].tobytes() for y in range(h) for c in range(3))
    sizes = [1, 1, 1]
    expected = _image_io._piz_raw_to_interleaved(raw, w, h, sizes)
    assert binding.piz_decode(raw, w, h, sizes) == expected


def test_piz_binding_unavailable_falls_back(monkeypatch):  # noqa: ANN001, ANN201
    monkeypatch.setattr(_image_io, "_piz_binding_loaded", False)
    monkeypatch.setattr(_image_io, "_piz_binding", None)
    monkeypatch.setattr(_image_io, "_get_piz_binding", lambda: None)
    img = read_exr(Path(__file__).parent / "data" / "piz_rgb.exr")
    assert img.shape == (16, 16, 3)
    assert img.dtype == np.float32


def test_piz_force_pure_python(monkeypatch):  # noqa: ANN001, ANN201
    monkeypatch.setenv("PYTANGA_FORCE_PURE_PYTHON", "1")
    monkeypatch.setattr(_image_io, "_piz_binding_loaded", False)
    monkeypatch.setattr(_image_io, "_piz_binding", None)
    assert _image_io._get_piz_binding() is None
    img = read_exr(Path(__file__).parent / "data" / "piz_rgb.exr")
    assert img.shape == (16, 16, 3)
    assert img.dtype == np.float32


def test_read_exr_progress() -> None:
    pixels = np.zeros((3, 4, 3), dtype=np.float64)
    fractions: list[float] = []
    img = read_exr(_exr_none(pixels, pixel_type=1), on_progress=fractions.append)
    assert img.shape == (3, 4, 3)
    assert fractions == [1 / 3, 2 / 3, 1.0]


def test_read_hdr_progress() -> None:
    fractions: list[float] = []
    data = _hdr(b"-Y 2 +X 2", _RED + _BRIGHT + _BLACK + _DEEP_BLUE)
    img = read_hdr(data, on_progress=fractions.append)
    assert img.shape == (2, 2, 3)
    assert fractions == [0.5, 1.0]


def test_register_loading_progress_handler() -> None:
    fractions: list[float] = []
    register_loading_progress_handler(fractions.append)
    try:
        read_hdr(_hdr(b"-Y 2 +X 2", _RED + _BRIGHT + _BLACK + _DEEP_BLUE))
        assert fractions == [0.5, 1.0]
    finally:
        register_loading_progress_handler(None)
