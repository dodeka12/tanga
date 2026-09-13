# Phase 5 — Binary WebSocket transport

## Goal

A length-prefixed **binary frame** for image pixel data, with Python encode/decode
helpers and the server/transport + frontend plumbing to send and receive it, so
images never travel as JSON/base64 on the live channel.

## Files

- New: `py/pytanga/viz/_image_wire.py` (encoder/decoder, pure + testable)
- Edit: `py/pytanga/viz/_transport.py` (add `send_bytes`)
- Edit: `py/pytanga/viz/_ports.py` (transport protocol + `ServerState`)
- Edit: `py/pytanga/viz/server.py` (add `push_bytes`)
- Edit: `py/pytanga/viz/templates/viewer.js` (`binaryType` + `onmessage` branch)
- New: `py/tests/viz/test_image_wire.py`

## Steps

- [x] **5.1 — `_image_wire.py` encoder/decoder**
  - `encode_image_frame(image_id, data: np.ndarray, dtype) -> bytes` and
    `decode_image_frame(buf: bytes) -> dict` implementing the README binary
    layout (little-endian header + raw C-contiguous bytes).
  - Validate magic/version/type and that `data_len` matches.

- [ ] **5.2 — transport + server bytes path**
  - `Transport.send_bytes(payload: bytes)`; `ServerState`/protocol extension;
    `server.push_bytes(data: bytes)` mirroring `push_raw` but `send_bytes`.
  - Thread-safe `run_coroutine_threadsafe` pattern as in `send`.

- [ ] **5.3 — frontend binary receive**
  - In `viewer.js`, set `ws.binaryType = 'arraybuffer'` and branch
    `onmessage`: `event.data instanceof ArrayBuffer` → decode via a `DataView`
    into `{id, width, height, channels, dtype, bytes}` and dispatch to the image
    renderer; otherwise keep the existing `JSON.parse` path.
  - Route the decoded frame to the image view by image id (store pending until
    the entity is built — see Phase 6/7).

- [ ] **5.4 — unit tests**
  - `py/tests/viz/test_image_wire.py`: round-trip for `uint8`/`uint16`/`float32`
    and 1/3/4 channels; header field correctness; bad magic raises.

## Validation

`uv run pytest py/tests/viz/test_image_wire.py -q && uv run ruff check py/pytanga/viz/_image_wire.py py/pytanga/viz/_transport.py py/pytanga/viz/server.py && node --check py/pytanga/viz/templates/viewer.js`

## Notes

- The binary frame is **self-describing** (id + dims + dtype in the header), so
  no separate JSON "announce" message is required for ordering.
- Keep `_image_wire.py` free of aiohttp/numpy-server imports so it is unit
  testable and reusable by the export path later.

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this work
touches, so the new code aligns with the documented architecture. If this work
introduces or changes architecture, update the developer docs.
