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
 *            fitHx:number, fitHy:number,
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

    const imageAspect = W / H;
    const aspect = Number(paneAspect) || imageAspect;
    const fillMode = fit === 'fill';
    // Base fit half-extents (NDC): how the full image letterboxes into the pane
    // at zoom=1.  `fit="fill"` stretches to fill (no letterbox).
    const hx0 = fillMode ? 1 : Math.min(1, imageAspect / aspect);
    const hy0 = fillMode ? 1 : Math.min(1, aspect / imageAspect);

    // Crop window (normalized image coordinates, v=0 at the top).  The window is
    // the *pane-shaped* portion of the image visible at this zoom: its half-width
    // and half-height shrink independently (bounded by the image), so zooming
    // scales the image up to fill the pane and then crops at the pane edges.
    let u0 = 0, v0 = 0, u1 = 1, v1 = 1;
    if (crop) {
        const zoom = Math.max(1, Number(crop.zoom) || 1);
        const pan = crop.pan || [0, 0];
        const halfU = 0.5 * Math.min(1, 1 / (hx0 * zoom));
        const halfV = 0.5 * Math.min(1, 1 / (hy0 * zoom));
        // Clamp the crop *centre* (not the edges) so the window keeps a constant
        // size and stays fully inside the image.  Panning is limited to the image
        // extent — it never stretches the image at the border.
        const cxN = _clamp(0.5 + (Number(pan[0]) || 0) * 0.5, halfU, 1 - halfU);
        const cyN = _clamp(0.5 + (Number(pan[1]) || 0) * 0.5, halfV, 1 - halfV);
        u0 = cxN - halfU;
        u1 = cxN + halfU;
        v0 = cyN - halfV;
        v1 = cyN + halfV;
    }

    // Map the crop onto the full frustum (`left↔u=0`, `right↔u=W`,
    // `top↔v=0`, `bottom↔v=H`).
    const left = left0 + u0 * (right0 - left0);
    const right = left0 + u1 * (right0 - left0);
    const top = top0 + v0 * (bottom0 - top0);
    const bottom = top0 + v1 * (bottom0 - top0);

    // Letterbox the crop window into the pane using its *own* pixel aspect
    // (not the full image's): as zoom grows, the window's aspect approaches the
    // pane's, so `hx`/`hy` grow toward 1 and the image fills the pane.
    const cropW = (u1 - u0) * W;
    const cropH = (v1 - v0) * H;
    const cropAspect = cropH > 0 ? cropW / cropH : imageAspect;

    let result;
    if (fillMode) {
        result = { left, right, top, bottom, near: n, far: Number(far), hx: 1, hy: 1 };
    } else if (aspect > cropAspect) {
        const k = aspect / cropAspect;
        const centerX = (left + right) / 2;
        const halfW = ((right - left) / 2) * k;
        result = {
            left: centerX - halfW,
            right: centerX + halfW,
            top,
            bottom,
            near: n,
            far: Number(far),
            hx: cropAspect / aspect,
            hy: 1,
        };
    } else if (aspect < cropAspect) {
        const k = cropAspect / aspect;
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
            hy: aspect / cropAspect,
        };
    } else {
        result = { left, right, top, bottom, near: n, far: Number(far), hx: 1, hy: 1 };
    }

    result.crop = { u0, v0, u1, v1 };
    result.fitHx = hx0;
    result.fitHy = hy0;
    return result;
}
