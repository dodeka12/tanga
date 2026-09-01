// SPDX-License-Identifier: Apache-2.0
// Copyright 2021 Christian Perwass
//
// Shared, pure camera-fit math used by the live viewer, the HTML export
// bootstrap, and (because it has no `three`/DOM dependency) the Node unit
// tests.  This is the single source of truth for the 2D ortho frustum and the
// finite-aspect computation — `view_mode.js`, `fit_camera.js`, and
// `js_apply_camera` (export) all call these, so the three can never drift
// apart.

/**
 * Return a finite aspect ratio (width / height), or NaN when the size is not
 * usable (zero, negative, or non-finite).  Callers must never write NaN into a
 * camera frustum, so they guard on this result.
 *
 * @param {number} width
 * @param {number} height
 * @returns {number}
 */
export function finiteAspect(width, height) {
    const w = Number(width);
    const h = Number(height);
    if (!Number.isFinite(w) || !Number.isFinite(h) || w <= 0 || h <= 0) {
        return NaN;
    }
    return w / h;
}

/**
 * Compute the orthographic left/right/top/bottom for a 2D camera.
 *
 * @param {number} xmin
 * @param {number} xmax
 * @param {number} ymin
 * @param {number} ymax
 * @param {boolean} uniform  letterbox (true) vs stretch-to-fill (false)
 * @param {number} borderPx  pixel margin (all modes)
 * @param {number} width     viewport width in CSS pixels
 * @param {number} height    viewport height in CSS pixels
 * @returns {{left:number, right:number, top:number, bottom:number}}
 */
export function orthoFrustum(xmin, xmax, ymin, ymax, uniform, borderPx, width, height) {
    const extX = Math.abs(xmax - xmin) || 10;
    const extY = Math.abs(ymax - ymin) || 10;
    const w = Number(width);
    const h = Number(height);
    const bp = borderPx || 0;
    const cw = w - 2 * bp;
    const ch = h - 2 * bp;

    if (uniform === false) {
        // Stretch-to-fill: the rectangle's width/height each fill the content
        // area (viewport inset by border_px), scaling X and Y independently
        // (non-uniform).  The camera is centered on the rectangle, so use
        // symmetric half-extents expanded back to the full viewport.
        const fX = cw > 0 ? w / cw : 1;
        const fY = ch > 0 ? h / ch : 1;
        return {
            left: -(extX / 2) * fX,
            right: (extX / 2) * fX,
            top: (extY / 2) * fY,
            bottom: -(extY / 2) * fY,
        };
    }

    // Undistorted letterboxing: a single world-units-per-pixel scale so the
    // full requested rectangle is contained.  An optional pixel border shrinks
    // the effective content area before the fit.
    const aspect = finiteAspect(w, h);
    const safeAspect = Number.isFinite(aspect) ? aspect : 1;
    const aspectContent = (cw > 0 && ch > 0) ? (cw / ch) : safeAspect;
    const fit = Math.max(extX / aspectContent, extY);
    // Expand the fitted content frustum back to the full viewport so the
    // border appears as extra margin (still uniform scale).
    const fitFull = (bp > 0 && cw > 0 && ch > 0) ? (fit * h / ch) : fit;

    return {
        left: -fitFull * safeAspect / 2,
        right: fitFull * safeAspect / 2,
        top: fitFull / 2,
        bottom: -fitFull / 2,
    };
}
