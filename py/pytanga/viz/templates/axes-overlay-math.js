// Tanga Viewer — pure math for the screen-space coordinate frame (axes overlay
// + grid underlay).  No `three`/DOM dependency; Node-testable.  The camera is
// passed as a plain `{left, right, top, bottom, zoom, x, y}` object.

import { niceLinearTicks, logTicks } from './nice-ticks.js';

/**
 * Compute the visible world rectangle of a 2D orthographic camera.
 *
 * @param {{left:number, right:number, top:number, bottom:number,
 *          zoom:number, x:number, y:number}} camera
 * @returns {{xmin:number, xmax:number, ymin:number, ymax:number}}
 */
export function visibleWorldRect(camera) {
    const zoom = Number(camera.zoom) || 1;
    const halfW = (Number(camera.right) - Number(camera.left)) / 2 / zoom;
    const halfH = (Number(camera.top) - Number(camera.bottom)) / 2 / zoom;
    const cx = Number(camera.x) || 0;
    const cy = Number(camera.y) || 0;
    return {
        xmin: cx - halfW,
        xmax: cx + halfW,
        ymin: cy - halfH,
        ymax: cy + halfH,
    };
}

function _worldToData(value, scale, base) {
    return scale === 'log' ? Math.pow(Number(base), value) : value;
}

function _dataToWorld(value, scale, base) {
    return scale === 'log' ? Math.log(value) / Math.log(Number(base)) : value;
}

/**
 * Convert a visible world rect to data bounds via the axis scales.
 *
 * @param {{xmin:number, xmax:number, ymin:number, ymax:number}} rect
 * @param {{xscale:string, yscale:string, base:number}} spec
 * @returns {{xlo:number, xhi:number, ylo:number, yhi:number}}
 */
export function worldToData(rect, spec) {
    return {
        xlo: _worldToData(rect.xmin, spec.xscale, spec.base),
        xhi: _worldToData(rect.xmax, spec.xscale, spec.base),
        ylo: _worldToData(rect.ymin, spec.yscale, spec.base),
        yhi: _worldToData(rect.ymax, spec.yscale, spec.base),
    };
}

function _axisTicks(lo, hi, scale, base, fmt, intervals, maxTicks) {
    return scale === 'log'
        ? logTicks(lo, hi, base, fmt)
        : niceLinearTicks(lo, hi, maxTicks, fmt, intervals);
}

/**
 * Map a world point to full-viewport screen pixels (top-down y).  This is the
 * same affine mapping the orthographic WebGL camera applies, so data, grid, and
 * frame stay aligned at every pan/zoom level.
 *
 * @param {{xmin:number, xmax:number, ymin:number, ymax:number}} rect
 * @param {number} wx  world x
 * @param {number} wy  world y
 * @param {number} width  viewport width in px
 * @param {number} height viewport height in px
 * @returns {{x:number, y:number}}
 */
export function worldToScreen(rect, wx, wy, width, height) {
    const w = Number(width) || 0;
    const h = Number(height) || 0;
    const xSpan = rect.xmax - rect.xmin;
    const ySpan = rect.ymax - rect.ymin;
    const x = xSpan === 0 ? w / 2 : ((wx - rect.xmin) / xSpan) * w;
    const y = ySpan === 0 ? h / 2 : ((rect.ymax - wy) / ySpan) * h;
    return { x, y };
}

/**
 * Compute the tick values + labels + full-viewport screen px for both axes.
 *
 * The per-axis tick count is derived from the live viewport: the number of
 * `min_tick_spacing_px`-wide slots that fit in the axis' content extent.  So
 * resizing or zooming re-densifies the grid.
 *
 * @param {{xmin:number, xmax:number, ymin:number, ymax:number}} rect
 * @param {{xscale:string, yscale:string, base:number, value_format:string,
 *          border_px:number, min_tick_spacing_px:number,
 *          intervals_x:Array<number>, intervals_y:Array<number>}} spec
 * @param {{width:number, height:number}} sizePx  full viewport size in px
 * @returns {{xTicks:Array<[number,string,number]>, yTicks:Array<[number,string,number]>}}
 */
export function ticksAndGrid(rect, spec, sizePx) {
    const data = worldToData(rect, spec);

    const width = Number(sizePx.width) || 0;
    const height = Number(sizePx.height) || 0;
    const border = Number(spec.border_px) || 0;
    const spacing = Math.max(1, Number(spec.min_tick_spacing_px) || 60);
    const maxTicksX = Math.max(2, Math.floor(Math.max(1, width - 2 * border) / spacing));
    const maxTicksY = Math.max(2, Math.floor(Math.max(1, height - 2 * border) / spacing));

    const xTicks = _axisTicks(data.xlo, data.xhi, spec.xscale, spec.base, spec.value_format, spec.intervals_x, maxTicksX);
    const yTicks = _axisTicks(data.ylo, data.yhi, spec.yscale, spec.base, spec.value_format, spec.intervals_y, maxTicksY);

    return {
        xTicks: xTicks.map(([value, label]) => {
            const world = _dataToWorld(value, spec.xscale, spec.base);
            return [value, label, worldToScreen(rect, world, 0, width, height).x];
        }),
        yTicks: yTicks.map(([value, label]) => {
            const world = _dataToWorld(value, spec.yscale, spec.base);
            return [value, label, worldToScreen(rect, 0, world, width, height).y];
        }),
    };
}
