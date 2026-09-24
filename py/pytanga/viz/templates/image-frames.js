// Tanga Viewer — pending binary image-frame store.
//
// Images arrive as raw binary WebSocket frames (see
// `py/pytanga/viz/_image_wire.py`).  The viewer decodes them into
// `{ id, width, height, channels, dtype, bytes }` and stores them here until
// the matching `image` entity is built, at which point the image renderer
// claims the frame (`takeImageFrame`) and uploads the texture.

const _pending = new Map();

export function storeImageFrame(frame) {
    _pending.set(frame.id, frame);
}

export function hasImageFrame(id) {
    return _pending.has(id);
}

export function takeImageFrame(id) {
    const frame = _pending.get(id);
    if (frame !== undefined) _pending.delete(id);
    return frame;
}

// Little-endian header after the 4-byte magic `"TGI\0"`:
//   version u8, type u8, idLen u8, [v2: codec u8], width u32, height u32,
//   channels u8, dtype u8, dataLen u64  — then id bytes, then the payload
//   (raw pixels, JPEG bytes, or zlib-compressed pixels).
export function decodeImageFrame(buffer) {
    const dv = new DataView(buffer);
    const magic = String.fromCharCode(
        dv.getUint8(0), dv.getUint8(1), dv.getUint8(2), dv.getUint8(3)
    );
    if (magic !== 'TGI\x00') throw new Error('bad image frame magic');

    const version = dv.getUint8(4);
    const type = dv.getUint8(5);
    const idLen = dv.getUint8(6);
    if (type !== 1) throw new Error('unexpected image frame type');

    let codec = 'raw';
    let width, height, channels, dtype, dataLen, idStart;
    if (version === 1) {
        width = dv.getUint32(7, true);
        height = dv.getUint32(11, true);
        channels = dv.getUint8(15);
        dtype = dv.getUint8(16);
        dataLen = Number(dv.getBigUint64(17, true));
        idStart = 25;
    } else if (version === 2) {
        const code = dv.getUint8(7);
        codec = code === 1 ? 'jpeg' : code === 2 ? 'zlib' : 'raw';
        width = dv.getUint32(8, true);
        height = dv.getUint32(12, true);
        channels = dv.getUint8(16);
        dtype = dv.getUint8(17);
        dataLen = Number(dv.getBigUint64(18, true));
        idStart = 26;
    } else {
        throw new Error('unsupported image frame version');
    }

    const id = new TextDecoder().decode(new Uint8Array(buffer, idStart, idLen));
    const dataStart = idStart + idLen;

    return {
        id,
        width,
        height,
        channels,
        dtype,
        codec,
        bytes: new Uint8Array(buffer, dataStart, dataLen),
    };
}
