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
//   version u8, type u8, idLen u8, width u32, height u32,
//   channels u8, dtype u8, dataLen u64  — then id bytes, then raw pixel bytes.
export function decodeImageFrame(buffer) {
    const dv = new DataView(buffer);
    const magic = String.fromCharCode(
        dv.getUint8(0), dv.getUint8(1), dv.getUint8(2), dv.getUint8(3)
    );
    if (magic !== 'TGI\x00') throw new Error('bad image frame magic');

    const version = dv.getUint8(4);
    const type = dv.getUint8(5);
    const idLen = dv.getUint8(6);
    if (version !== 1) throw new Error('unsupported image frame version');
    if (type !== 1) throw new Error('unexpected image frame type');
    const width = dv.getUint32(7, true);
    const height = dv.getUint32(11, true);
    const channels = dv.getUint8(15);
    const dtype = dv.getUint8(16);
    const dataLen = Number(dv.getBigUint64(17, true));

    const idStart = 25;
    const id = new TextDecoder().decode(new Uint8Array(buffer, idStart, idLen));
    const dataStart = idStart + idLen;

    return {
        id,
        width,
        height,
        channels,
        dtype,
        bytes: new Uint8Array(buffer, dataStart, dataLen),
    };
}
