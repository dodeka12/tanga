# Phase 2 — `_backgroundTexture` keep-previous + `registerImageFrameConsumer` fallback

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-architecture.md` — "Image
> background" and the `image-frames.js` store API in the image-transport
> section).  This mirrors the existing `renderers/image.js` fallback; no
> architecture change.

## Goal

Make the background renderer distinguish "no pixel frame has arrived yet" from
"decoded an actual (possibly empty) image": when no frame is pending for a
`source:"data"` image, `_backgroundTexture()` resolves `null` instead of a blank
`DataTexture`.  The fresh-pane path then fills in via a one-shot
`registerImageFrameConsumer`, and the reuse path keeps the previous texture.
This is what lets Phase 3 stop re-sending unchanged frames without blanking the
pane.

## Files

- Edit: `py/pytanga/viz/templates/renderers/image-background.js`

## Steps

- [x] **2.1 — Import the consumer hook.**
  - Change the `../image-frames.js` import (currently
    `import { hasImageFrame, takeImageFrame } from '../image-frames.js';`) to also
    import `registerImageFrameConsumer`.

- [x] **2.2 — Return `null` when no frame is pending (data source).**
  - In `_backgroundTexture()` (~line 92–96), replace
    ```js
    const frame = hasImageFrame(img.id) ? takeImageFrame(img.id) : null;
    return makeEncodedTexture(img, frame);
    ```
    with
    ```js
    const frame = hasImageFrame(img.id) ? takeImageFrame(img.id) : null;
    if (!frame) return Promise.resolve(null);   // no pixel frame yet
    return makeEncodedTexture(img, frame);
    ```
  - `url`/`tiled`/`stream` paths are unchanged (they never consult `_pending`).

- [x] **2.3 — Fresh-pane fallback in `createImageBackground()`.**
  - In `createImageBackground()` (~line 113–115), when the resolved texture is
    `null` (frame still on the wire), register a one-shot consumer that uploads
    the texture once the frame lands — mirroring `renderers/image.js:351–355`:
    ```js
    _backgroundTexture(img).then((tex) => {
        if (tex) {
            material.uniforms.uImage.value = tex;
        } else {
            registerImageFrameConsumer(img.id, (frame) => {
                makeEncodedTexture(img, frame).then((t) => {
                    if (t) material.uniforms.uImage.value = t;
                });
            });
        }
    });
    ```

- [x] **2.4 — Confirm the reuse path keeps the previous texture.**
  - `updateImageBackground()` already does
    `_backgroundTexture(img).then((tex) => { if (tex) mat.uniforms.uImage.value = tex; })`;
    with `_backgroundTexture` now resolving `null` when the frame is absent, the
    uniform is left untouched and the previous texture stays visible.  No edit
    needed — verify and note it in the commit.

## Validation

`node js/dev/tests/check-syntax.mjs`

(Behavioural gate — manual: run the `serve-smoke.py` + `reconcile-smoke.mjs`
smoke; "New noise" must still swap the background, and a "Reconnect" (Phase 1.3)
must still render it.)

## Notes

- `makeEncodedTexture(img, null)` previously returned a blank `DataTexture`
  (`makeDataTexture` fills `emptyTypedArray`), which is why the reuse path could
  blank an unchanged background once frames stop being re-sent.
- This also removes the background-side asymmetry flagged in
  `_input/pytanga-background-image-blank-pane.md` (the same
  frame-arrives-after-entity race `renderers/image.js` already tolerates).
