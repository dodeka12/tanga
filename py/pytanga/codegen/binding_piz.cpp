// SPDX-License-Identifier: Apache-2.0
// Copyright 2021 Christian Perwass
//
// binding_piz - a dependency-free pybind11 extension that decodes OpenEXR PIZ
// (Huffman + Haar wavelet + range) scanline chunks.
//
// The decode algorithm is a direct port of the BSD-3-Clause OpenEXR / tinyexr
// reference implementations (ImfHuf.cpp / ImfWav.cpp / tinyexr's DecompressPiz),
// which themselves derive from Christian Rouet's PIZ image-format routines.
// It is byte-identical to the pure-Python fallback in
// `pytanga/viz/_image_io.py` (`_piz_uncompress`).

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <cstdint>
#include <cstring>
#include <stdexcept>
#include <string>
#include <vector>

namespace py = pybind11;

// OpenEXR PIZ is little-endian; the reference decoder bails out on big-endian
// platforms.  Guard the same way for GCC/Clang (MSVC targets are little-endian).
#if defined(__BYTE_ORDER__) && (__BYTE_ORDER__ == __ORDER_BIG_ENDIAN__)
#error "binding_piz requires a little-endian platform"
#endif

namespace {

const int HUF_DECBITS = 14;
const int HUF_DECSIZE = 1 << HUF_DECBITS;
const int HUF_DECMASK = HUF_DECSIZE - 1;
const int HUF_ENCSIZE = (1 << 16) + 1;
const int SHORT_ZEROCODE_RUN = 59;
const int LONG_ZEROCODE_RUN = 63;
const int SHORTEST_LONG_RUN = 2 + LONG_ZEROCODE_RUN - SHORT_ZEROCODE_RUN;

const int USHORT_RANGE = 1 << 16;
const int BITMAP_SIZE = USHORT_RANGE >> 3;

uint16_t readU16(const uint8_t* b) {
    return (uint16_t)((uint16_t)b[0] | ((uint16_t)b[1] << 8));
}

uint32_t readU32(const uint8_t* b) {
    return (uint32_t)b[0] | ((uint32_t)b[1] << 8) | ((uint32_t)b[2] << 16) |
           ((uint32_t)b[3] << 24);
}

struct HufDec {
    int len;  // code length (short codes) or 0 (long codes)
    int lit;  // literal (short codes) or number of long-code candidates
    int* p;   // nullptr (short) or array of long-code symbol indices
};

uint64_t hufLength(uint64_t code) { return code & 63; }
uint64_t hufCode(uint64_t code) { return code >> 6; }

uint64_t getBits(int nBits, uint64_t& c, int& lc, const uint8_t*& in) {
    while (lc < nBits) {
        c = (c << 8) | *in++;
        lc += 8;
    }
    lc -= nBits;
    return (c >> lc) & ((1ull << nBits) - 1);
}

void hufCanonicalCodeTable(uint64_t* hcode) {
    uint64_t n[59];
    for (int i = 0; i <= 58; ++i) n[i] = 0;
    for (int i = 0; i < HUF_ENCSIZE; ++i) n[hcode[i]] += 1;

    uint64_t c = 0;
    for (int i = 58; i > 0; --i) {
        uint64_t nc = (c + n[i]) >> 1;
        n[i] = c;
        c = nc;
    }

    for (int i = 0; i < HUF_ENCSIZE; ++i) {
        int l = (int)hcode[i];
        if (l > 0) hcode[i] = (uint64_t)l | (n[l]++ << 6);
    }
}

void hufUnpackEncTable(
    const uint8_t*& pcode, int ni, int im, int iM, uint64_t* hcode) {
    std::memset(hcode, 0, sizeof(uint64_t) * HUF_ENCSIZE);

    const uint8_t* p = pcode;
    const uint8_t* start = pcode;
    uint64_t c = 0;
    int lc = 0;

    for (; im <= iM; im++) {
        if (p - start > ni) throw std::runtime_error("unexpected end of Huffman table");
        uint64_t l = getBits(6, c, lc, p);
        hcode[im] = l;

        if (l == (uint64_t)LONG_ZEROCODE_RUN) {
            if (p - start > ni) throw std::runtime_error("unexpected end of Huffman table");
            int zerun = (int)getBits(8, c, lc, p) + SHORTEST_LONG_RUN;
            if (im + zerun > iM + 1) throw std::runtime_error("Huffman table too long");
            while (zerun--) hcode[im++] = 0;
            im--;
        } else if (l >= (uint64_t)SHORT_ZEROCODE_RUN) {
            int zerun = (int)l - SHORT_ZEROCODE_RUN + 2;
            if (im + zerun > iM + 1) throw std::runtime_error("Huffman table too long");
            while (zerun--) hcode[im++] = 0;
            im--;
        }
    }

    pcode = p;
    hufCanonicalCodeTable(hcode);
}

void hufBuildDecTable(const uint64_t* hcode, int im, int iM, HufDec* hdecod) {
    for (; im <= iM; im++) {
        uint64_t c = hufCode(hcode[im]);
        int l = (int)hufLength(hcode[im]);

        if (c >> l) throw std::runtime_error("invalid Huffman code");

        if (l > HUF_DECBITS) {
            HufDec* pl = hdecod + (c >> (l - HUF_DECBITS));
            if (pl->len) throw std::runtime_error("invalid Huffman table");
            pl->lit++;

            if (pl->p) {
                int* p = pl->p;
                pl->p = new int[pl->lit];
                for (int i = 0; i < pl->lit - 1; ++i) pl->p[i] = p[i];
                delete[] p;
            } else {
                pl->p = new int[1];
            }
            pl->p[pl->lit - 1] = im;
        } else if (l) {
            HufDec* pl = hdecod + (c << (HUF_DECBITS - l));
            for (uint64_t i = (1ull << (HUF_DECBITS - l)); i > 0; i--, pl++) {
                if (pl->len || pl->p) throw std::runtime_error("invalid Huffman table");
                pl->len = l;
                pl->lit = im;
            }
        }
    }
}

void hufFreeDecTable(HufDec* hdecod) {
    for (int i = 0; i < HUF_DECSIZE; ++i) {
        if (hdecod[i].p) delete[] hdecod[i].p;
    }
}

void hufDecode(
    const uint64_t* hcode,
    const HufDec* hdecod,
    const uint8_t* in,
    int ni,
    int rlc,
    int no,
    uint16_t* out) {
    uint64_t c = 0;
    int lc = 0;
    uint16_t* outb = out;
    uint16_t* oe = out + no;
    const uint8_t* ie = in + (ni + 7) / 8;

    auto getChar = [&]() {
        c = (c << 8) | *in++;
        lc += 8;
    };
    auto getCode = [&](int po) {
        if (po == rlc) {
            if (lc < 8) getChar();
            lc -= 8;
            unsigned char cs = (unsigned char)(c >> lc);
            if (out + cs > oe) throw std::runtime_error("Huffman data too long");
            if (out - 1 < outb) throw std::runtime_error("Huffman data too short");
            uint16_t s = out[-1];
            while (cs-- > 0) *out++ = s;
        } else {
            if (out >= oe) throw std::runtime_error("Huffman data too long");
            *out++ = (uint16_t)po;
        }
    };

    while (in < ie) {
        getChar();
        while (lc >= HUF_DECBITS) {
            const HufDec pl = hdecod[(c >> (lc - HUF_DECBITS)) & HUF_DECMASK];

            if (pl.len) {
                lc -= pl.len;
                if (lc < 0) throw std::runtime_error("invalid Huffman code");
                getCode(pl.lit);
            } else {
                if (!pl.p) throw std::runtime_error("invalid Huffman code");

                int j;
                for (j = 0; j < pl.lit; j++) {
                    int l = (int)hufLength(hcode[pl.p[j]]);
                    while (lc < l && in < ie) getChar();
                    if (lc >= l) {
                        if (hufCode(hcode[pl.p[j]]) ==
                            ((c >> (lc - l)) & ((1ull << l) - 1))) {
                            lc -= l;
                            getCode(pl.p[j]);
                            break;
                        }
                    }
                }
                if (j == pl.lit) throw std::runtime_error("invalid Huffman code");
            }
        }
    }

    int i = (8 - ni) & 7;
    c >>= i;
    lc -= i;
    while (lc > 0) {
        const HufDec pl = hdecod[(c << (HUF_DECBITS - lc)) & HUF_DECMASK];
        if (!pl.len) throw std::runtime_error("invalid Huffman code");
        lc -= pl.len;
        if (lc < 0) throw std::runtime_error("invalid Huffman code");
        getCode(pl.lit);
    }

    if (out - outb != no) throw std::runtime_error("Huffman data too short");
}

void hufUncompress(const uint8_t* compressed, int nCompressed, uint16_t* raw, int nRaw) {
    if (nCompressed < 20) {
        if (nRaw != 0) throw std::runtime_error("truncated Huffman data");
        return;
    }

    int im = (int)readU32(compressed);
    int iM = (int)readU32(compressed + 4);
    int nBits = (int)readU32(compressed + 12);

    if (im < 0 || im >= HUF_ENCSIZE || iM < 0 || iM >= HUF_ENCSIZE)
        throw std::runtime_error("invalid Huffman table");

    const uint8_t* ptr = compressed + 20;
    uint64_t nBytes = ((uint64_t)nBits + 7) / 8;
    if (ptr + nBytes > compressed + nCompressed)
        throw std::runtime_error("truncated Huffman data");

    std::vector<uint64_t> hcode(HUF_ENCSIZE);
    std::vector<HufDec> hdec(HUF_DECSIZE);
    std::memset(hdec.data(), 0, sizeof(HufDec) * HUF_DECSIZE);

    hufUnpackEncTable(ptr, nCompressed - (int)(ptr - compressed), im, iM, hcode.data());

    if (nBits > 8 * (int)(nCompressed - (ptr - compressed)))
        throw std::runtime_error("invalid Huffman bit count");

    hufBuildDecTable(hcode.data(), im, iM, hdec.data());

    try {
        hufDecode(hcode.data(), hdec.data(), ptr, nBits, iM, nRaw, raw);
    } catch (...) {
        hufFreeDecTable(hdec.data());
        throw;
    }
    hufFreeDecTable(hdec.data());
}

const int NBITS = 16;
const int A_OFFSET = 1 << (NBITS - 1);
const int MOD_MASK = (1 << NBITS) - 1;

void wdec14(uint16_t l, uint16_t h, uint16_t& a, uint16_t& b) {
    short ls = (short)l;
    short hs = (short)h;
    int hi = hs;
    int ai = ls + (hi & 1) + (hi >> 1);
    short as = (short)ai;
    short bs = (short)(ai - hi);
    a = (uint16_t)as;
    b = (uint16_t)bs;
}

void wdec16(uint16_t l, uint16_t h, uint16_t& a, uint16_t& b) {
    int m = l;
    int d = h;
    int bb = (m - (d >> 1)) & MOD_MASK;
    int aa = (d + bb - A_OFFSET) & MOD_MASK;
    b = (uint16_t)bb;
    a = (uint16_t)aa;
}

void wav2Decode(uint16_t* in, int nx, int ox, int ny, int oy, uint16_t mx) {
    bool w14 = (mx < (1 << 14));
    int n = (nx > ny) ? ny : nx;
    int p = 1;
    int p2;

    while (p <= n) p <<= 1;
    p >>= 1;
    p2 = p;
    p >>= 1;

    while (p >= 1) {
        uint16_t* py = in;
        uint16_t* ey = in + oy * (ny - p2);
        int oy1 = oy * p;
        int oy2 = oy * p2;
        int ox1 = ox * p;
        int ox2 = ox * p2;
        uint16_t i00, i01, i10, i11;

        for (; py <= ey; py += oy2) {
            uint16_t* px = py;
            uint16_t* ex = py + ox * (nx - p2);

            for (; px <= ex; px += ox2) {
                uint16_t* p01 = px + ox1;
                uint16_t* p10 = px + oy1;
                uint16_t* p11 = p10 + ox1;

                if (w14) {
                    wdec14(*px, *p10, i00, i10);
                    wdec14(*p01, *p11, i01, i11);
                    wdec14(i00, i01, *px, *p01);
                    wdec14(i10, i11, *p10, *p11);
                } else {
                    wdec16(*px, *p10, i00, i10);
                    wdec16(*p01, *p11, i01, i11);
                    wdec16(i00, i01, *px, *p01);
                    wdec16(i10, i11, *p10, *p11);
                }
            }

            if (nx & p) {
                uint16_t* p10 = px + oy1;
                if (w14) wdec14(*px, *p10, i00, *p10);
                else wdec16(*px, *p10, i00, *p10);
                *px = i00;
            }
        }

        if (ny & p) {
            uint16_t* px = py;
            uint16_t* ex = py + ox * (nx - p2);
            for (; px <= ex; px += ox2) {
                uint16_t* p01 = px + ox1;
                if (w14) wdec14(*px, *p01, i00, *p01);
                else wdec16(*px, *p01, i00, *p01);
                *px = i00;
            }
        }

        p2 = p;
        p >>= 1;
    }
}

uint16_t reverseLutFromBitmap(const uint8_t* bitmap, uint16_t* lut) {
    int k = 0;
    for (int i = 0; i < USHORT_RANGE; ++i) {
        if (i == 0 || (bitmap[i >> 3] & (1 << (i & 7)))) lut[k++] = (uint16_t)i;
    }
    int n = k - 1;
    while (k < USHORT_RANGE) lut[k++] = 0;
    return (uint16_t)n;
}

void applyLut(const uint16_t* lut, uint16_t* data, int nData) {
    for (int i = 0; i < nData; ++i) data[i] = lut[data[i]];
}

std::string piz_decode_impl(
    const std::string& chunk, int width, int n_lines, const std::vector<int>& sizes) {
    const uint8_t* inPtr = reinterpret_cast<const uint8_t*>(chunk.data());
    size_t inLen = chunk.size();

    int total = 0;
    for (int s : sizes) total += s;
    uint64_t n_shorts = (uint64_t)width * (uint64_t)n_lines * (uint64_t)total;

    // Raw (uncompressed) fallback: chunk is channel-planar-per-scanline data.
    if ((uint64_t)inLen == n_shorts * 2) {
        const uint16_t* arr = reinterpret_cast<const uint16_t*>(chunk.data());
        std::vector<uint16_t> out(n_shorts);
        size_t out_pos = 0;
        for (int y = 0; y < n_lines; ++y) {
            for (int x = 0; x < width; ++x) {
                size_t prefix = 0;
                for (size_t ci = 0; ci < sizes.size(); ++ci) {
                    int s = sizes[ci];
                    for (int sub = 0; sub < s; ++sub) {
                        size_t src = (size_t)y * (width * total) + prefix + (size_t)x * s + sub;
                        out[out_pos++] = arr[src];
                    }
                    prefix += (size_t)width * s;
                }
            }
        }
        return std::string(reinterpret_cast<const char*>(out.data()), out.size() * 2);
    }

    if (inLen < 4) throw std::runtime_error("truncated PIZ data");

    uint16_t minNonZero = readU16(inPtr);
    uint16_t maxNonZero = readU16(inPtr + 2);
    size_t pos = 4;

    std::vector<uint8_t> bitmap(BITMAP_SIZE, 0);
    if (minNonZero <= maxNonZero) {
        if (maxNonZero >= BITMAP_SIZE) throw std::runtime_error("invalid PIZ bitmap");
        size_t n_bytes = (size_t)(maxNonZero - minNonZero + 1);
        if (pos + n_bytes > inLen) throw std::runtime_error("truncated PIZ bitmap");
        std::memcpy(bitmap.data() + minNonZero, inPtr + pos, n_bytes);
        pos += n_bytes;
    } else if (!(minNonZero == (BITMAP_SIZE - 1) && maxNonZero == 0)) {
        throw std::runtime_error("invalid PIZ bitmap");
    }

    std::vector<uint16_t> lut(USHORT_RANGE, 0);
    uint16_t maxValue = reverseLutFromBitmap(bitmap.data(), lut.data());

    if (pos + 4 > inLen) throw std::runtime_error("truncated PIZ data");
    int length = (int)readU32(inPtr + pos);
    pos += 4;
    if (pos + (size_t)length > inLen) throw std::runtime_error("truncated PIZ Huffman data");

    std::vector<uint16_t> tmp(n_shorts);
    hufUncompress(inPtr + pos, length, tmp.data(), (int)n_shorts);

    size_t start = 0;
    for (int s : sizes) {
        for (int j = 0; j < s; ++j) {
            wav2Decode(tmp.data() + start + j, width, s, n_lines, width * s, maxValue);
        }
        start += (size_t)width * n_lines * s;
    }

    applyLut(lut.data(), tmp.data(), (int)n_shorts);

    std::vector<uint16_t> out(n_shorts);
    size_t out_pos = 0;
    for (int y = 0; y < n_lines; ++y) {
        for (int x = 0; x < width; ++x) {
            size_t channel_start = 0;
            for (size_t ci = 0; ci < sizes.size(); ++ci) {
                int s = sizes[ci];
                for (int sub = 0; sub < s; ++sub) {
                    size_t idx = channel_start + (size_t)y * (width * s) + (size_t)x * s + sub;
                    out[out_pos++] = tmp[idx];
                }
                channel_start += (size_t)width * n_lines * s;
            }
        }
    }

    return std::string(reinterpret_cast<const char*>(out.data()), out.size() * 2);
}

}  // namespace

py::bytes piz_decode(py::bytes chunk, int width, int n_lines, std::vector<int> sizes) {
    std::string result = piz_decode_impl(chunk, width, n_lines, sizes);
    return py::bytes(result.data(), result.size());
}

PYBIND11_MODULE(binding_piz, m) {
    m.doc() = "Dependency-free OpenEXR PIZ (Huffman + wavelet + range) decoder";
    m.def(
        "piz_decode",
        &piz_decode,
        py::arg("chunk"),
        py::arg("width"),
        py::arg("n_lines"),
        py::arg("sizes"),
        "Decode a PIZ chunk into interleaved little-endian uint16 pixel bytes.");
}
