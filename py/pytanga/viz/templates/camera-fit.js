// SPDX-License-Identifier: Apache-2.0
// Copyright 2021 Christian Perwass
//
// Shared camera-fit math used by the live viewer, the HTML export bootstrap,
// and (because it has no `three`/DOM dependency) the Node unit tests.  This is
// the single source of truth for the 2D ortho frustum and the finite-aspect
// computation — `view_mode.js`, `fit_camera.js`, and `js_apply_camera`
// (export) all call these, so the three can never drift apart.  Everything
// here is `three`/DOM-free; `applyOrthoFrustum` additionally mutates a camera
// object (`left`/`right`/`top`/`bottom`) but remains dependency-free.

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
 * @param {string} stretch  "fit" (letterbox) | "fill" | "fill_x" | "fill_y"
 * @param {number} borderPx  pixel margin (all modes)
 * @param {number} width     viewport width in CSS pixels
 * @param {number} height    viewport height in CSS pixels
 * @returns {{left:number, right:number, top:number, bottom:number}}
 */
export function orthoFrustum(xmin, xmax, ymin, ymax, stretch, borderPx, width, height) {
    const extX = Math.abs(xmax - xmin) || 10;
    const extY = Math.abs(ymax - ymin) || 10;
    const w = Number(width);
    const h = Number(height);
    const bp = borderPx || 0;
    const cw = w - 2 * bp;
    const ch = h - 2 * bp;
    const mode = stretch || 'fit';

    if (mode === 'fill') {
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

    // fill_x / fill_y: one axis fills the content area at a uniform scale;
    // the other keeps the aspect ratio and may over- or under-fill.
    if (mode === 'fill_x' && cw > 0 && ch > 0) {
        const fullW = extX * w / cw;
        const fullH = extX * h / cw;
        return {
            left: -fullW / 2,
            right: fullW / 2,
            top: fullH / 2,
            bottom: -fullH / 2,
        };
    }
    if (mode === 'fill_y' && cw > 0 && ch > 0) {
        const fullW = extY * w / ch;
        const fullH = extY * h / ch;
        return {
            left: -fullW / 2,
            right: fullW / 2,
            top: fullH / 2,
            bottom: -fullH / 2,
        };
    }

    // Undistorted letterboxing (fit, the default): a single
    // world-units-per-pixel scale so the full requested rectangle is
    // contained.  An optional pixel border shrinks the effective content area
    // before the fit.
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

/**
 * Recompute an orthographic camera's `left`/`right`/`top`/`bottom` for the
 * given viewport size.  Recomputed from the stored fit
 * (``camera.userData._view2d``) when available; otherwise the current full
 * height is preserved.  Never writes NaN/Infinity — a corrupt frustum is
 * reset to a sane default box.
 *
 * @param {object} camera
 * @param {number} width   viewport width in CSS pixels
 * @param {number} height  viewport height in CSS pixels
 */
export function applyOrthoFrustum(camera, width, height) {
    const aspect = finiteAspect(width, height);
    const v2d = camera.userData?._view2d;
    const finiteRect = v2d
        && Number.isFinite(v2d.xmin) && Number.isFinite(v2d.xmax)
        && Number.isFinite(v2d.ymin) && Number.isFinite(v2d.ymax);

    if (finiteRect) {
        const f = orthoFrustum(
            v2d.xmin, v2d.xmax, v2d.ymin, v2d.ymax,
            v2d.stretch || 'fit', v2d.border_px || 0, width, height
        );
        camera.left = f.left;
        camera.right = f.right;
        camera.top = f.top;
        camera.bottom = f.bottom;
        return;
    }

    // Fall back to preserving the current full height, but never propagate a
    // non-finite/corrupt frustum (Math.max(NaN, …) === NaN).
    const extX = Math.abs(camera.right - camera.left);
    const extY = Math.abs(camera.top - camera.bottom);
    if (!Number.isFinite(extX) || !Number.isFinite(extY) || extX <= 0 || extY <= 0) {
        const height = 10;  // sane default full height
        camera.left = -height * aspect / 2;
        camera.right = height * aspect / 2;
        camera.top = height / 2;
        camera.bottom = -height / 2;
        return;
    }

    const fit = Math.max(extX / aspect, extY);
    camera.left = -fit * aspect / 2;
    camera.right = fit * aspect / 2;
    camera.top = fit / 2;
    camera.bottom = -fit / 2;
}
