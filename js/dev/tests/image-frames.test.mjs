// Tanga — unit tests for the binary image-frame decoder (node --test).
import test from 'node:test';
import assert from 'node:assert/strict';
import { decodeImageFrame } from '../../../py/pytanga/viz/templates/image-frames.js';

// Build a little-endian frame by hand (magic "TGI\0" + header + id + payload).
function buildFrame({ version = 2, codec = 0, width = 2, height = 3, channels = 1, dtype = 0, id = 'img1', payload = new Uint8Array([1, 2, 3, 4, 5, 6]) }) {
    const idBytes = new TextEncoder().encode(id);
    const headerSize = version === 1 ? 21 : 22;
    const total = 4 + headerSize + idBytes.length + payload.length;
    const buf = new ArrayBuffer(total);
    const dv = new DataView(buf);

    dv.setUint8(0, 0x54); // 'T'
    dv.setUint8(1, 0x47); // 'G'
    dv.setUint8(2, 0x49); // 'I'
    dv.setUint8(3, 0x00);
    dv.setUint8(4, version);
    dv.setUint8(5, 1); // type = image
    dv.setUint8(6, idBytes.length);
    if (version === 1) {
        dv.setUint32(7, width, true);
        dv.setUint32(11, height, true);
        dv.setUint8(15, channels);
        dv.setUint8(16, dtype);
        dv.setBigUint64(17, BigInt(payload.length), true);
    } else {
        dv.setUint8(7, codec);
        dv.setUint32(8, width, true);
        dv.setUint32(12, height, true);
        dv.setUint8(16, channels);
        dv.setUint8(17, dtype);
        dv.setBigUint64(18, BigInt(payload.length), true);
    }

    const idStart = 4 + headerSize;
    new Uint8Array(buf, idStart, idBytes.length).set(idBytes);
    new Uint8Array(buf, idStart + idBytes.length, payload.length).set(payload);
    return buf;
}

test('v2 raw frame decodes with codec raw', () => {
    const payload = new Uint8Array([10, 20, 30, 40, 50, 60]);
    const decoded = decodeImageFrame(buildFrame({ codec: 0, payload }));
    assert.equal(decoded.id, 'img1');
    assert.equal(decoded.width, 2);
    assert.equal(decoded.height, 3);
    assert.equal(decoded.channels, 1);
    assert.equal(decoded.dtype, 0);
    assert.equal(decoded.codec, 'raw');
    assert.deepEqual([...decoded.bytes], [...payload]);
});

test('v2 jpeg frame decodes with codec jpeg', () => {
    const payload = new Uint8Array([0xff, 0xd8, 0xff, 0xd9]);
    const decoded = decodeImageFrame(buildFrame({ codec: 1, payload }));
    assert.equal(decoded.codec, 'jpeg');
    assert.deepEqual([...decoded.bytes], [...payload]);
});

test('v2 zlib frame decodes with codec zlib', () => {
    const payload = new Uint8Array([1, 2, 3]);
    const decoded = decodeImageFrame(buildFrame({ codec: 2, payload }));
    assert.equal(decoded.codec, 'zlib');
    assert.deepEqual([...decoded.bytes], [...payload]);
});

test('v1 frame still decodes as codec raw', () => {
    const payload = new Uint8Array([7, 8, 9]);
    const decoded = decodeImageFrame(buildFrame({ version: 1, payload }));
    assert.equal(decoded.id, 'img1');
    assert.equal(decoded.codec, 'raw');
    assert.equal(decoded.width, 2);
    assert.equal(decoded.height, 3);
    assert.deepEqual([...decoded.bytes], [...payload]);
});

test('unsupported version throws', () => {
    assert.throws(() => decodeImageFrame(buildFrame({ version: 9 })), /unsupported image frame version/);
});
