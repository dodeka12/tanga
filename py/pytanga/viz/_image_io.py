# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Dependency-free readers for Radiance RGBE (``.hdr``) and OpenEXR (``.exr``).

Both readers return raw linear ``float32`` arrays of shape ``(H, W, C)`` with no
tone mapping or colour-space conversion, using only numpy and the standard
library — so loading HDR images never requires Pillow or the ``OpenEXR`` package.
"""

from __future__ import annotations

import io
import os
import struct
import zlib
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

import numpy as np

__all__ = ["read_exr", "read_hdr", "register_loading_progress_handler"]

ProgressHandler = Callable[[float], None]

_registered_progress_handler: ProgressHandler | None = None


def register_loading_progress_handler(handler: ProgressHandler | None) -> None:
    """Register (or clear) a handler called with load progress in ``[0, 1]``.

    ``read_exr`` and ``read_hdr`` call the handler once per decoded chunk or
    scanline with the fraction completed.  A per-call ``on_progress`` argument
    overrides the registered handler.
    """
    global _registered_progress_handler
    _registered_progress_handler = handler


def _effective_progress(on_progress: ProgressHandler | None) -> ProgressHandler | None:
    return on_progress if on_progress is not None else _registered_progress_handler


def _as_buffer(source: str | Path | bytes) -> bytes:
    if isinstance(source, bytes):
        return source
    return Path(source).read_bytes()


# --------------------------------------------------------------------------
# Radiance RGBE (`.hdr` / `.pic`)
# --------------------------------------------------------------------------


def read_hdr(
    source: str | Path | bytes, *, on_progress: ProgressHandler | None = None
) -> np.ndarray:
    """Read a Radiance ``.hdr``/``.pic`` image into a ``float32`` ``(H, W, 3)`` array.

    Supports the ``#?RADIANCE``/``#?RGBE`` header, the standard ``-Y H +X W``
    resolution line (plus the sign/order variants), and the flat and new
    (adaptive) RLE pixel encodings.  Values are linear RGB; a shared zero
    exponent maps to ``0.0``.

    ``on_progress`` (or the handler registered with
    :func:`register_loading_progress_handler`) is called with a fraction in
    ``[0, 1]`` as each scanline is decoded.
    """
    data = _as_buffer(source)
    progress = _effective_progress(on_progress)

    header_end = data.find(b"\n\n")
    if header_end < 0:
        raise ValueError("not a Radiance HDR file (missing header terminator)")
    header = data[:header_end].decode("latin-1", errors="replace")
    if not (header.startswith("#?RADIANCE") or header.startswith("#?RGBE")):
        raise ValueError("not a Radiance HDR file (bad magic)")

    rest = data[header_end + 2 :]
    nl = rest.find(b"\n")
    if nl < 0:
        raise ValueError("Radiance HDR file is missing the resolution line")
    resolution = rest[:nl].strip().decode("latin-1", errors="replace")
    pixels = rest[nl + 1 :]

    height, width, x_first, flip_y, flip_x = _parse_hdr_resolution(resolution)

    lines = width if x_first else height
    line_length = height if x_first else width
    raw = _decode_hdr_scanlines(pixels, lines, line_length, on_progress=progress)

    img = raw.transpose(1, 0, 2) if x_first else raw
    if flip_y:
        img = img[::-1, :, :]
    if flip_x:
        img = img[:, ::-1, :]
    return np.ascontiguousarray(img, dtype=np.float32)


def _parse_hdr_resolution(line: str) -> tuple[int, int, bool, bool, bool]:
    """Parse the ``-Y H +X W`` resolution line.

    Returns ``(height, width, x_first, flip_y, flip_x)`` where ``x_first`` means
    the X token precedes the Y token (column-major storage), and the flip flags
    describe the file's row/column direction relative to standard top-left
    ordering.
    """
    parts = line.split()
    if len(parts) != 4:
        raise ValueError(f"unexpected Radiance HDR resolution line: {line!r}")

    axes: dict[str, tuple[str, int]] = {}
    order: list[str] = []
    for i in range(0, 4, 2):
        token = parts[i]
        if len(token) != 2 or token[0] not in "+-" or token[1].upper() not in "XY":
            raise ValueError(f"bad Radiance HDR axis token: {token!r}")
        axis = token[1].upper()
        if axis in axes:
            raise ValueError(f"duplicate Radiance HDR axis {axis!r}")
        axes[axis] = (token[0], int(parts[i + 1]))
        order.append(axis)

    if "X" not in axes or "Y" not in axes:
        raise ValueError("Radiance HDR resolution line is missing X or Y")
    x_sign, width = axes["X"]
    y_sign, height = axes["Y"]
    return height, width, order[0] == "X", y_sign == "+", x_sign == "-"


def _decode_hdr_scanlines(
    data: bytes,
    lines: int,
    line_length: int,
    *,
    on_progress: ProgressHandler | None = None,
) -> np.ndarray:
    out = np.empty((lines, line_length, 3), dtype=np.float32)
    buf = io.BytesIO(data)
    for line in range(lines):
        head = buf.read(4)
        if len(head) < 4:
            raise ValueError("truncated Radiance HDR pixel data")
        if head[0] == 2 and head[1] == 2 and not (head[2] & 0x80):
            # New (adaptive) RLE scanline: header `2, 2, width_hi, width_lo`.
            if ((head[2] << 8) | head[3]) != line_length:
                raise ValueError("Radiance HDR RLE scanline width mismatch")
            scan = _decode_hdr_rle_scanline(buf, line_length)
        else:
            # Flat scanline (the reference reader also treats a non-new-RLE
            # scanline header as flat, so the legacy old RLE is read as flat).
            buf.seek(-4, io.SEEK_CUR)
            scan = buf.read(line_length * 4)
            if len(scan) < line_length * 4:
                raise ValueError("truncated Radiance HDR pixel data")
        out[line] = _rgbe_to_rgb(scan)
        if on_progress is not None:
            on_progress((line + 1) / lines)
    return out


def _decode_hdr_rle_scanline(buf: io.BytesIO, width: int) -> bytes:
    """Decode one new-RLE scanline: four interleaved component streams."""
    scan = bytearray(width * 4)
    for comp in range(4):
        ptr = comp
        remaining = width
        while remaining > 0:
            n = buf.read(1)
            if not n:
                raise ValueError("truncated Radiance HDR RLE scanline")
            count = n[0]
            if count > 128:
                value = buf.read(1)
                if not value:
                    raise ValueError("truncated Radiance HDR RLE run")
                count -= 128
                if count == 0 or count > remaining:
                    raise ValueError("invalid Radiance HDR RLE run length")
                for _ in range(count):
                    scan[ptr] = value[0]
                    ptr += 4
            else:
                if count == 0 or count > remaining:
                    raise ValueError("invalid Radiance HDR RLE literal length")
                for _ in range(count):
                    value = buf.read(1)
                    if not value:
                        raise ValueError("truncated Radiance HDR RLE literal")
                    scan[ptr] = value[0]
                    ptr += 4
            remaining -= count
    return bytes(scan)


def _rgbe_to_rgb(scan: bytes) -> np.ndarray:
    """Convert a buffer of RGBE quads to linear float32 RGB."""
    quad = np.frombuffer(scan, dtype=np.uint8).reshape(-1, 4).astype(np.float32)
    mantissa = quad[:, :3] + 0.5
    exponent = quad[:, 3]
    # value = (m + 0.5) * 2^(e - 128) / 256 = (m + 0.5) * 2^(e - 136).
    scale = np.where(exponent != 0, np.exp2(exponent - 136.0), 0.0)
    return mantissa * scale[:, None]


# --------------------------------------------------------------------------
# OpenEXR (`.exr`)
# --------------------------------------------------------------------------

_EXR_MAGIC = 20000630  # 0x01312f76, bytes 76 2f 31 01

# compression code -> scanlines per chunk
_EXR_LINES_PER_CHUNK = {
    0: 1,
    1: 1,
    2: 1,
    3: 16,
    4: 32,
    5: 16,
    6: 32,
    7: 32,
    8: 32,
    9: 256,
}

# pixel type code -> bytes per sample
_EXR_SAMPLE_BYTES = {0: 4, 1: 2, 2: 4}  # UINT, HALF, FLOAT


def read_exr(
    source: str | Path | bytes, *, on_progress: ProgressHandler | None = None
) -> np.ndarray:
    """Read a scanline OpenEXR image into a ``float32`` ``(H, W, C)`` array.

    Supports the lossless codecs ``NONE``/``RLE``/``ZIPS``/``ZIP``/``PIZ`` and
    the ``UINT``/``HALF``/``FLOAT`` channel types (sampling ``1``).  Returns the
    ``dataWindow`` extent with raw linear values; ``displayWindow`` cropping is
    ignored.

    ``on_progress`` (or the handler registered with
    :func:`register_loading_progress_handler`) is called with a fraction in
    ``[0, 1]`` as each scanline block is decoded.
    """
    data = _as_buffer(source)
    progress = _effective_progress(on_progress)
    if len(data) < 8:
        raise ValueError("truncated OpenEXR file")
    magic, version = struct.unpack_from("<2I", data, 0)
    if magic != _EXR_MAGIC:
        raise ValueError("not an OpenEXR file (bad magic)")
    if version & 0x1000 or version & 0x800 or version & 0x200:
        raise ValueError("unsupported OpenEXR file (tiled/deep/multi-part)")

    header, offset = _parse_exr_header(data, 8)
    if (
        "channels" not in header
        or "compression" not in header
        or "dataWindow" not in header
    ):
        raise ValueError("OpenEXR file is missing required attributes")

    channels = _parse_exr_channels(header["channels"])
    for name, _ptype, xs, ys in channels:
        if xs != 1 or ys != 1:
            raise ValueError(f"subsampled OpenEXR channel {name!r} is unsupported")

    if len(header["compression"]) != 1:
        raise ValueError("invalid OpenEXR compression attribute")
    compression = header["compression"][0]
    min_x, min_y, max_x, max_y = struct.unpack("<4i", header["dataWindow"])
    width = max_x - min_x + 1
    height = max_y - min_y + 1
    line_order = header["lineOrder"][0] if "lineOrder" in header else 0

    lines_per_chunk = _EXR_LINES_PER_CHUNK.get(compression)
    if lines_per_chunk is None:
        raise ValueError(f"unsupported OpenEXR compression codec {compression}")
    n_chunks = (height + lines_per_chunk - 1) // lines_per_chunk
    if len(data) < offset + 8 * n_chunks:
        raise ValueError("truncated OpenEXR line offset table")
    offsets = struct.unpack_from(f"<{n_chunks}q", data, offset)

    bytes_per_pixel = sum(_EXR_SAMPLE_BYTES[ptype] for _name, ptype, _x, _y in channels)
    out = np.empty((height, width, len(channels)), dtype=np.float32)

    for i, chunk_off in enumerate(offsets):
        if chunk_off > 0:
            if len(data) < chunk_off + 8:
                raise ValueError("truncated OpenEXR chunk")
            y, size = struct.unpack_from("<2i", data, chunk_off)
            chunk = data[chunk_off + 8 : chunk_off + 8 + size]
            if len(chunk) < size:
                raise ValueError("truncated OpenEXR chunk")

            if line_order == 0:  # INCREASING_Y
                r0 = y - min_y
                n_lines = min(lines_per_chunk, height - r0)
                rows = list(range(r0, r0 + n_lines))
            else:  # DECREASING_Y
                r0 = y - min_y
                n_lines = min(lines_per_chunk, r0 + 1)
                rows = list(range(r0, r0 - n_lines, -1))
            if n_lines > 0:
                raw = _decode_exr_chunk(
                    chunk, compression, channels, bytes_per_pixel, width, n_lines
                )
                plane = _unpack_exr_raw(raw, width, n_lines, channels, bytes_per_pixel)
                for j, row in enumerate(rows):
                    out[row] = plane[j]

        if progress is not None:
            progress((i + 1) / n_chunks)

    keep = _select_exr_channels([name for name, _ptype, _x, _y in channels])
    return np.ascontiguousarray(out[:, :, keep], dtype=np.float32)


def _parse_exr_header(data: bytes, offset: int) -> tuple[dict[str, bytes], int]:
    """Parse the attribute list; return ``{name: value}`` and the end offset."""
    header: dict[str, bytes] = {}
    while True:
        end = data.find(b"\0", offset)
        if end < 0:
            raise ValueError("truncated OpenEXR header")
        name = data[offset:end].decode("latin-1")
        offset = end + 1
        if name == "":
            return header, offset

        end = data.find(b"\0", offset)
        if end < 0:
            raise ValueError("truncated OpenEXR header")
        offset = end + 1
        if len(data) < offset + 4:
            raise ValueError("truncated OpenEXR header")
        size = struct.unpack_from("<i", data, offset)[0]
        offset += 4
        if size < 0 or offset + size > len(data):
            raise ValueError("truncated OpenEXR header value")
        header[name] = data[offset : offset + size]
        offset += size


def _parse_exr_channels(value: bytes) -> list[tuple[str, int, int, int]]:
    """Parse a ``chlist`` value into ``[(name, pixel_type, x_sampling, y_sampling)]``."""
    channels: list[tuple[str, int, int, int]] = []
    offset = 0
    while True:
        end = value.find(b"\0", offset)
        if end < 0:
            raise ValueError("truncated OpenEXR channel list")
        name = value[offset:end].decode("latin-1")
        offset = end + 1
        if name == "":
            return channels
        if len(value) < offset + 16:
            raise ValueError("truncated OpenEXR channel entry")
        pixel_type = struct.unpack_from("<i", value, offset)[0]
        offset += 4
        offset += 4  # 1 byte pLinear + 3 reserved bytes
        x_sampling = struct.unpack_from("<i", value, offset)[0]
        offset += 4
        y_sampling = struct.unpack_from("<i", value, offset)[0]
        offset += 4
        channels.append((name, pixel_type, x_sampling, y_sampling))


def _select_exr_channels(names: list[str]) -> list[int]:
    """Pick the output channels: ``R, G, B`` (plus ``A``) when present, else all."""
    if "R" in names and "G" in names and "B" in names:
        selected = [names.index(n) for n in ("R", "G", "B")]
        if "A" in names:
            selected.append(names.index("A"))
        return selected
    return list(range(min(4, len(names))))


def _decode_exr_chunk(
    chunk: bytes,
    compression: int,
    channels: list[tuple[str, int, int, int]],
    bytes_per_pixel: int,
    width: int,
    n_lines: int,
) -> bytes:
    """Decompress one scanline block into raw interleaved pixel bytes."""
    if compression == 0:  # NONE
        return chunk
    if compression == 1:  # RLE
        return _decode_exr_rle(chunk, bytes_per_pixel, width)
    if compression in (2, 3):  # ZIPS / ZIP
        return _decode_exr_zip(chunk, bytes_per_pixel)
    if compression == 4:  # PIZ
        return _decode_exr_piz(chunk, channels, width, n_lines)
    raise ValueError(f"unsupported OpenEXR compression codec {compression}")


def _unpack_exr_raw(
    raw: bytes,
    width: int,
    n_lines: int,
    channels: list[tuple[str, int, int, int]],
    bytes_per_pixel: int,
) -> np.ndarray:
    """Convert raw interleaved pixel bytes to a ``(n_lines, width, C)`` float32 plane."""
    n_pixels = n_lines * width
    expected = n_pixels * bytes_per_pixel
    if len(raw) < expected:
        raise ValueError("truncated OpenEXR pixel data")
    arr = np.frombuffer(raw[:expected], dtype=np.uint8).reshape(
        n_pixels, bytes_per_pixel
    )
    out = np.empty((n_lines, width, len(channels)), dtype=np.float32)
    sample_offset = 0
    for ci, (_name, pixel_type, _xs, _ys) in enumerate(channels):
        nbytes = _EXR_SAMPLE_BYTES[pixel_type]
        slab = arr[:, sample_offset : sample_offset + nbytes]
        sample_offset += nbytes
        if pixel_type == 1:  # HALF
            values = np.frombuffer(slab.tobytes(), dtype="<f2").astype(np.float32)
        elif pixel_type == 2:  # FLOAT
            values = np.frombuffer(slab.tobytes(), dtype="<f4")
        else:  # UINT
            values = np.frombuffer(slab.tobytes(), dtype="<u4").astype(np.float32)
        out[:, :, ci] = values.reshape(n_lines, width)
    return out


def _decode_exr_rle(chunk: bytes, bytes_per_pixel: int, width: int) -> bytes:
    """Decode an OpenEXR RLE scanline into raw interleaved pixel bytes."""
    out = bytearray()
    expected = width * bytes_per_pixel
    i = 0
    while i < len(chunk):
        control = chunk[i]
        i += 1
        if control & 0x80:  # signed negative -> run of `256 - control` bytes
            count = 256 - control
            if i >= len(chunk):
                raise ValueError("truncated OpenEXR RLE run")
            value = chunk[i]
            i += 1
            out.extend(bytes([value]) * count)
        else:  # literal of `control + 1` bytes
            count = control + 1
            if i + count > len(chunk):
                raise ValueError("truncated OpenEXR RLE literal")
            out.extend(chunk[i : i + count])
            i += count
    if len(out) != expected:
        raise ValueError("OpenEXR RLE decompressed to the wrong size")
    return bytes(out)


def _decode_exr_zip(chunk: bytes, bytes_per_pixel: int) -> bytes:
    """Decode a ZIP/ZIPS chunk (2-byte size + zlib) and undo the pixel reorder."""
    if len(chunk) < 2:
        raise ValueError("truncated OpenEXR ZIP chunk")
    expected = struct.unpack_from("<H", chunk, 0)[0]
    raw = zlib.decompress(chunk[2:])
    if len(raw) != expected:
        raise ValueError("OpenEXR ZIP decompressed to the wrong size")
    return _reorder_exr_pixels(raw, bytes_per_pixel)


def _reorder_exr_pixels(raw: bytes, pixel_size: int) -> bytes:
    """Swap the two halves of each pixel (the OpenEXR ZIP/PIZ byte reorder)."""
    half = pixel_size // 2
    if half == 0 or len(raw) % pixel_size:
        return raw
    arr = np.frombuffer(raw, dtype=np.uint8).reshape(-1, pixel_size)
    return np.concatenate([arr[:, half:], arr[:, :half]], axis=1).tobytes()


# PIZ (Huffman + wavelet + range) decompression.  This is a direct port of the
# decoder in the OpenEXR / tinyexr reference implementations (BSD-3-Clause),
# which themselves derive from Christian Rouet's PIZ image-format routines.
_HUF_DECBITS = 14
_HUF_DECSIZE = 1 << _HUF_DECBITS
_HUF_DECMASK = _HUF_DECSIZE - 1
_HUF_ENCSIZE = (1 << 16) + 1
_SHORT_ZEROCODE_RUN = 59
_LONG_ZEROCODE_RUN = 63
_SHORTEST_LONG_RUN = 2 + _LONG_ZEROCODE_RUN - _SHORT_ZEROCODE_RUN


class _BitReader:
    """MSB-first bit reader over a byte string.

    ``_c`` is kept masked to 128 bits so that the shift/and operations stay
    O(1) instead of growing with the stream (which would make decoding O(n²)).
    """

    _MASK = (1 << 128) - 1

    def __init__(self, data: bytes) -> None:
        self._data = data
        self._pos = 0
        self._c = 0
        self._lc = 0

    @property
    def pos(self) -> int:
        return self._pos

    def shift(self) -> None:
        if self._pos >= len(self._data):
            raise ValueError("truncated OpenEXR Huffman data")
        self._c = ((self._c << 8) | self._data[self._pos]) & self._MASK
        self._pos += 1
        self._lc += 8

    def bits(self, nbits: int) -> int:
        while self._lc < nbits:
            self.shift()
        self._lc -= nbits
        return (self._c >> self._lc) & ((1 << nbits) - 1)


class _HufDec:
    __slots__ = ("len", "lit", "p")

    def __init__(self) -> None:
        self.len = 0
        self.lit = 0
        self.p: list[int] | None = None


def _huf_uncompress(compressed: bytes, n_raw: int) -> np.ndarray:
    """Decode a PIZ Huffman stream into *n_raw* unsigned 16-bit values."""
    if len(compressed) < 20:
        if n_raw == 0:
            return np.empty(0, dtype=np.uint16)
        raise ValueError("truncated OpenEXR Huffman data")

    im = int.from_bytes(compressed[0:4], "little")
    iM = int.from_bytes(compressed[4:8], "little")
    n_bits = int.from_bytes(compressed[12:16], "little")
    if not (0 <= im < _HUF_ENCSIZE and 0 <= iM < _HUF_ENCSIZE):
        raise ValueError("invalid OpenEXR Huffman table")

    reader = _BitReader(compressed[20:])
    hcode = [0] * _HUF_ENCSIZE

    idx = im
    while idx <= iM:
        length = reader.bits(6)
        if length == _LONG_ZEROCODE_RUN:
            zero_run = reader.bits(8) + _SHORTEST_LONG_RUN
        elif length >= _SHORT_ZEROCODE_RUN:
            zero_run = length - _SHORT_ZEROCODE_RUN + 2
        else:
            zero_run = 0
        for _ in range(zero_run):
            hcode[idx] = 0
            idx += 1
        if zero_run:
            idx -= 1
        else:
            hcode[idx] = length
        idx += 1

    counts = [0] * 59
    for code_len in hcode:
        counts[code_len] += 1
    c = 0
    for i in range(58, 0, -1):
        nxt = (c + counts[i]) >> 1
        counts[i] = c
        c = nxt
    for i in range(_HUF_ENCSIZE):
        length = hcode[i]
        if length > 0:
            hcode[i] = length | (counts[length] << 6)
            counts[length] += 1

    hdecod = [_HufDec() for _ in range(_HUF_DECSIZE)]
    for i in range(im, iM + 1):
        value = hcode[i] >> 6
        length = hcode[i] & 63
        if value >> length:
            raise ValueError("invalid OpenEXR Huffman code")
        if length > _HUF_DECBITS:
            slot = hdecod[value >> (length - _HUF_DECBITS)]
            if slot.len:
                raise ValueError("invalid OpenEXR Huffman table")
            slot.lit += 1
            if slot.p is None:
                slot.p = [i]
            else:
                slot.p.append(i)
        elif length:
            start = value << (_HUF_DECBITS - length)
            for j in range(1 << (_HUF_DECBITS - length)):
                slot = hdecod[start + j]
                if slot.len or slot.p:
                    raise ValueError("invalid OpenEXR Huffman table")
                slot.len = length
                slot.lit = i

    code_data = compressed[20 + reader.pos : 20 + reader.pos + (n_bits + 7) // 8]
    return _huf_decode(hdecod, hcode, code_data, n_bits, iM, n_raw)


def _huf_decode(
    hdecod: list[_HufDec],
    hcode: list[int],
    code_data: bytes,
    n_bits: int,
    rlc: int,
    n_raw: int,
) -> np.ndarray:
    reader = _BitReader(code_data)
    n_bytes = len(code_data)
    out = np.empty(n_raw, dtype=np.uint16)
    oi = 0

    def get_code(lit: int) -> bool:
        nonlocal oi
        if lit == rlc:
            if reader._lc < 8:
                if reader.pos >= n_bytes:
                    return False
                reader.shift()
            reader._lc -= 8
            run = (reader._c >> reader._lc) & 0xFF
            if oi + run > n_raw or oi == 0:
                return False
            out[oi : oi + run] = out[oi - 1]
            oi += run
        else:
            if oi >= n_raw:
                return False
            out[oi] = lit
            oi += 1
        return True

    while reader.pos < n_bytes:
        reader.shift()
        while reader._lc >= _HUF_DECBITS:
            slot = hdecod[(reader._c >> (reader._lc - _HUF_DECBITS)) & _HUF_DECMASK]
            if slot.len:
                reader._lc -= slot.len
                if not get_code(slot.lit):
                    raise ValueError("invalid OpenEXR Huffman stream")
                continue
            if slot.p is None:
                raise ValueError("invalid OpenEXR Huffman stream")
            matched = False
            for candidate in slot.p:
                length = hcode[candidate] & 63
                while reader._lc < length and reader.pos < n_bytes:
                    reader.shift()
                if reader._lc >= length:
                    code = hcode[candidate] >> 6
                    if code == (
                        (reader._c >> (reader._lc - length)) & ((1 << length) - 1)
                    ):
                        reader._lc -= length
                        if not get_code(candidate):
                            raise ValueError("invalid OpenEXR Huffman stream")
                        matched = True
                        break
            if not matched:
                raise ValueError("invalid OpenEXR Huffman stream")

    i = (8 - n_bits) & 7
    reader._c >>= i
    reader._lc -= i
    while reader._lc > 0:
        slot = hdecod[(reader._c << (_HUF_DECBITS - reader._lc)) & _HUF_DECMASK]
        if not slot.len:
            raise ValueError("invalid OpenEXR Huffman stream")
        reader._lc -= slot.len
        if not get_code(slot.lit):
            raise ValueError("invalid OpenEXR Huffman stream")

    if oi != n_raw:
        raise ValueError("OpenEXR Huffman decoded to the wrong size")
    return out


def _wdec14_np(lo: np.ndarray, hi: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Vectorized ``wdec14``: returns ``(a, b)`` as ``uint16`` arrays."""
    ls = lo.astype(np.int16).astype(np.int32)
    hs = hi.astype(np.int16).astype(np.int32)
    ai = ls + (hs & 1) + (hs >> 1)
    return (ai & 0xFFFF).astype(np.uint16), ((ai - hs) & 0xFFFF).astype(np.uint16)


def _wdec16_np(lo: np.ndarray, hi: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Vectorized ``wdec16``: returns ``(a, b)`` as ``uint16`` arrays."""
    m = lo.astype(np.int32)
    d = hi.astype(np.int32)
    b = (m - (d >> 1)) & 0xFFFF
    a = (d + b - 0x8000) & 0xFFFF
    return a.astype(np.uint16), b.astype(np.uint16)


def _wav2_decode(
    arr: np.ndarray, base: int, nx: int, ox: int, ny: int, oy: int, mx: int
) -> None:
    """Inverse 2D wavelet on the sub-plane at *base* of a flat ``uint16`` array."""
    plane = np.lib.stride_tricks.as_strided(
        arr[base:], shape=(ny, nx), strides=(oy * arr.itemsize, ox * arr.itemsize)
    )
    w14 = mx < (1 << 14)
    dec = _wdec14_np if w14 else _wdec16_np
    n = nx if nx < ny else ny
    p = 1
    while p <= n:
        p <<= 1
    p >>= 1
    p2 = p
    p >>= 1
    while p >= 1:
        ys = slice(0, ny - p2 + 1, p2)
        ys_hi = slice(p, ny - p2 + 1 + p, p2)
        xs = slice(0, nx - p2 + 1, p2)
        xs_hi = slice(p, nx - p2 + 1 + p, p2)

        a00 = plane[ys, xs]
        a10 = plane[ys_hi, xs]
        a01 = plane[ys, xs_hi]
        a11 = plane[ys_hi, xs_hi]

        i00, i10 = dec(a00, a10)
        i01, i11 = dec(a01, a11)
        r00, r01 = dec(i00, i01)
        r10, r11 = dec(i10, i11)

        plane[ys, xs] = r00
        plane[ys, xs_hi] = r01
        plane[ys_hi, xs] = r10
        plane[ys_hi, xs_hi] = r11

        if nx & p:
            col = (nx // p2) * p2
            col_top, col_bottom = dec(plane[ys, col], plane[ys_hi, col])
            plane[ys, col] = col_top
            plane[ys_hi, col] = col_bottom
        if ny & p:
            row = (ny // p2) * p2
            row_left, row_right = dec(plane[row, xs], plane[row, xs_hi])
            plane[row, xs] = row_left
            plane[row, xs_hi] = row_right

        p2 = p
        p >>= 1


_piz_binding_loaded = False
_piz_binding: Any = None  # None == unavailable after first probe


def _get_piz_binding() -> Any | None:
    """Return the compiled ``binding_piz`` module, or ``None`` if unavailable.

    The probe runs once (per process) and caches both success and failure, so
    the lookup does not repeat a build/load attempt for every chunk.
    """
    global _piz_binding_loaded, _piz_binding
    if _piz_binding_loaded:
        return _piz_binding
    _piz_binding_loaded = True
    if os.environ.get("PYTANGA_FORCE_PURE_PYTHON") == "1":
        return None
    try:
        from pytanga.codegen._piz_cache import get_or_build_piz

        _piz_binding = get_or_build_piz()
    except Exception:
        _piz_binding = None
    return _piz_binding


def _piz_uncompress(
    chunk: bytes, channels: list[tuple[str, int, int, int]], width: int, n_lines: int
) -> bytes:
    """Decode a PIZ chunk into interleaved pixel bytes (OpenEXR/tinyexr port)."""
    sizes = [1 if pixel_type == 1 else 2 for _name, pixel_type, _x, _y in channels]
    n_shorts = width * n_lines * sum(sizes)

    # OpenEXR stores the packed (channel-planar-per-scanline) data raw when
    # compression would not shrink it; convert it to interleaved bytes.
    if len(chunk) == n_shorts * 2:
        return _piz_raw_to_interleaved(chunk, width, n_lines, sizes)

    # Fast path: the compiled C++ binding (byte-identical to the numpy decode).
    binding = _get_piz_binding()
    if binding is not None:
        try:
            return cast(bytes, binding.piz_decode(chunk, width, n_lines, sizes))
        except Exception:
            pass  # decode/load error -> fall back to numpy

    if len(chunk) < 4:
        raise ValueError("truncated OpenEXR PIZ data")
    min_nz = int.from_bytes(chunk[0:2], "little")
    max_nz = int.from_bytes(chunk[2:4], "little")
    pos = 4

    bitmap = bytearray(8192)
    if min_nz <= max_nz:
        if max_nz >= 8192:
            raise ValueError("invalid OpenEXR PIZ bitmap")
        n_bytes = max_nz - min_nz + 1
        if pos + n_bytes > len(chunk):
            raise ValueError("truncated OpenEXR PIZ bitmap")
        bitmap[min_nz : min_nz + n_bytes] = chunk[pos : pos + n_bytes]
        pos += n_bytes
    elif not (min_nz == 8191 and max_nz == 0):
        raise ValueError("invalid OpenEXR PIZ bitmap")

    lut = [0] * 65536
    k = 0
    for i in range(65536):
        if i == 0 or (bitmap[i >> 3] & (1 << (i & 7))):
            lut[k] = i
            k += 1
    max_value = k - 1

    if pos + 4 > len(chunk):
        raise ValueError("truncated OpenEXR PIZ data")
    length = int.from_bytes(chunk[pos : pos + 4], "little")
    pos += 4
    if pos + length > len(chunk):
        raise ValueError("truncated OpenEXR PIZ Huffman data")

    tmp = _huf_uncompress(chunk[pos : pos + length], n_shorts)

    starts = []
    off = 0
    for s in sizes:
        starts.append(off)
        off += width * n_lines * s
    for ci, s in enumerate(sizes):
        base = starts[ci]
        for j in range(s):
            _wav2_decode(tmp, base + j, width, s, n_lines, width * s, max_value)

    tmp = np.asarray(lut, dtype=np.uint16)[tmp]

    total = sum(sizes)
    interleaved = np.empty((n_lines, width, total), dtype=np.uint16)
    col = 0
    for ci, s in enumerate(sizes):
        start = starts[ci]
        plane = tmp[start : start + width * n_lines * s].reshape(n_lines, width, s)
        interleaved[:, :, col : col + s] = plane
        col += s
    return interleaved.tobytes()


def _piz_raw_to_interleaved(
    chunk: bytes, width: int, n_lines: int, sizes: list[int]
) -> bytes:
    """Convert an uncompressed PIZ buffer (channel-planar-per-scanline) to interleaved."""
    total = sum(sizes)
    arr = np.frombuffer(chunk, dtype=np.uint16).reshape(n_lines, width * total)
    interleaved = np.empty((n_lines, width, total), dtype=np.uint16)
    col = 0
    for s in sizes:
        interleaved[:, :, col : col + s] = arr[
            :, width * col : width * col + width * s
        ].reshape(n_lines, width, s)
        col += s
    return interleaved.tobytes()


def _decode_exr_piz(
    chunk: bytes, channels: list[tuple[str, int, int, int]], width: int, n_lines: int
) -> bytes:
    return _piz_uncompress(chunk, channels, width, n_lines)
