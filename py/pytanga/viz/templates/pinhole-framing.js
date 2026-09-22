// SPDX-License-Identifier: Apache-2.0
// Copyright 2021 Christian Perwass
//
// Pure pinhole-projection + framing math.  `pinholeFraming` converts
// distortion-free intrinsics into an off-center perspective frustum AND the
// background image's letterbox half-extents, driven by a `fit` policy, so the
// projection and the image can never diverge.  An optional `crop` ({zoom, pan})
// folds a 2D viewport transform into both, as a crop window over the image.
// No `three`/DOM dependency.

function _clamp(v, lo, hi) {
    return Math.min(Math.max(v, lo), hi);
}

/**
 * Compute the off-center frustum bounds and the background letterbox for a
 * pinhole camera.
 *
 * Intrinsics use the OpenCV convention (image origin top-left, y down):
 * `u = fx·(X/Z) + cx`, `v = fy·(Y/Z) + cy`.
 *
 * @param {number} fx, fy, cx, cy  intrinsics (pixels)
 * @param {number} width, height   image size (pixels)
 * @param {number} near, far       clipping planes
 * @param {number} paneAspect      viewport width / height
 * @param {string} fit             "fit" (letterbox) | "fill" (stretch)
 * @param {{zoom:number, pan:[number,number]}|null} crop  optional viewport crop
 * @returns {{left:number, right:number, top:number, bottom:number,
 *            near:number, far:number, hx:number, hy:number,
 *            crop:{u0:number, v0:number, u1:number, v1:number}}}
 */
export function pinholeFraming(fx, fy, cx, cy, width, height, near, far, paneAspect, fit, crop) {
    const fxN = Number(fx);
    const fyN = Number(fy);
    const n = Number(near);
    const W = Number(width);
    const H = Number(height);

    // Full-image frustum bounds.
    const left0 = -(cx * n) / fxN;
    const right0 = ((W - cx) * n) / fxN;
    const top0 = (cy * n) / fyN;
    const bottom0 = -((H - cy) * n) / fyN;

    // Crop window (normalized image coordinates, v=0 at the top).
    let u0 = 0, v0 = 0, u1 = 1, v1 = 1;
    if (crop) {
        const zoom = Math.max(1, Number(crop.zoom) || 1);
        const pan = crop.pan || [0, 0];
        const half = 0.5 / zoom;
        // Clamp the crop *centre* (not the edges) so the window keeps a
        // constant size and stays fully inside the image.  Panning is limited
        // to the image extent — it never stretches the image at the border.
        const cxN = _clamp(0.5 + (Number(pan[0]) || 0) * 0.5, half, 1 - half);
        const cyN = _clamp(0.5 + (Number(pan[1]) || 0) * 0.5, half, 1 - half);
        u0 = cxN - half;
        u1 = cxN + half;
        v0 = cyN - half;
        v1 = cyN + half;
    }

    // Map the crop onto the full frustum (`left↔u=0`, `right↔u=W`,
    // `top↔v=0`, `bottom↔v=H`).
    const left = left0 + u0 * (right0 - left0);
    const right = left0 + u1 * (right0 - left0);
    const top = top0 + v0 * (bottom0 - top0);
    const bottom = top0 + v1 * (bottom0 - top0);

    const imageAspect = W / H;
    const aspect = Number(paneAspect) || imageAspect;

    let result;
    if (fit === 'fill') {
        result = { left, right, top, bottom, near: n, far: Number(far), hx: 1, hy: 1 };
    } else if (aspect > imageAspect) {
        const k = aspect / imageAspect;
        const centerX = (left + right) / 2;
        const halfW = ((right - left) / 2) * k;
        result = {
            left: centerX - halfW,
            right: centerX + halfW,
            top,
            bottom,
            near: n,
            far: Number(far),
            hx: imageAspect / aspect,
            hy: 1,
        };
    } else if (aspect < imageAspect) {
        const k = imageAspect / aspect;
        const centerY = (top + bottom) / 2;
        const halfH = ((top - bottom) / 2) * k;
        result = {
            left,
            right,
            top: centerY + halfH,
            bottom: centerY - halfH,
            near: n,
            far: Number(far),
            hx: 1,
            hy: aspect / imageAspect,
        };
    } else {
        result = { left, right, top, bottom, near: n, far: Number(far), hx: 1, hy: 1 };
    }

    result.crop = { u0, v0, u1, v1 };
    return result;
}
