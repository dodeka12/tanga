// Tanga Viewer — pending binary image-frame store.
//
// Images arrive as raw binary WebSocket frames (see
// `py/pytanga/viz/_image_wire.py`).  The viewer decodes them into
// `{ id, width, height, channels, dtype, bytes }` and stores them here until
// the matching `image` entity is built, at which point the image renderer
// claims the frame (`takeImageFrame`) and uploads the texture.

const _pending = new Map();
// image id → list of one-shot consumers invoked when the frame arrives (the
// image entity was built before its pixel frame — a wire-order race).
const _pendingConsumers = new Map();

export function storeImageFrame(frame) {
    _pending.set(frame.id, frame);
    const consumers = _pendingConsumers.get(frame.id);
    if (consumers) {
        _pendingConsumers.delete(frame.id);
        for (const consume of consumers) consume(frame);
    }
}

export function hasImageFrame(id) {
    return _pending.has(id);
}

export function takeImageFrame(id) {
    const frame = _pending.get(id);
    if (frame !== undefined) _pending.delete(id);
    return frame;
}

// Return the frame with `id` without removing it (for textures shared across
// several consumers, e.g. one surface texture applied to multiple entities).
export function peekImageFrame(id) {
    return _pending.get(id);
}

// Remove a frame (and any pending one-shot consumers) from the store.  Used
// when an entity that shared its frames via `peekImageFrame` is removed, so the
// store does not grow across add/remove cycles.
export function removeImageFrame(id) {
    _pending.delete(id);
    _pendingConsumers.delete(id);
}

// Resolve the authoritative pixel layout for a data texture.  The decoded
// frame's own header (width/height/channels/dtype) wins when a frame is
// present, falling back to `img` metadata only when it is not.  `img` can be
// stale (a one-shot consumer registered from an older message), whereas the
// frame is self-describing — trusting it prevents e.g. decoding a 2048×1535
// frame into a 1×1 placeholder-sized texture.
export function resolveFrameFormat(img, frame) {
    const meta = img || {};
    return {
        width: (frame && frame.width) || meta.width,
        height: (frame && frame.height) || meta.height,
        channels: (frame && frame.channels) || meta.channels || 1,
        dtype: (frame && frame.dtype) ?? meta.dtype ?? 0,
    };
}

// Register a one-shot consumer to be invoked when the frame with `id` arrives.
export function registerImageFrameConsumer(id, consume) {
    if (!_pendingConsumers.has(id)) _pendingConsumers.set(id, []);
    _pendingConsumers.get(id).push(consume);
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
