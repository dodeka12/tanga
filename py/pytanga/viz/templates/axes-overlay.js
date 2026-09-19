// Tanga Viewer — screen-space coordinate axes frame renderer (overlay layer).
// Draws the plot rectangle, tick marks, value labels, and axis name labels as
// SVG into the per-pane overlay region.  DOM + the shared pure math; no `three`.

import { visibleWorldRect, ticksAndGrid } from './axes-overlay-math.js';

const SVG_NS = 'http://www.w3.org/2000/svg';

function _num(value, fallback) {
    const n = Number(value);
    return Number.isFinite(n) ? n : fallback;
}

function _color(style, fallback) {
    return style && style.color ? style.color : fallback;
}

function _off2d(style, fallback) {
    const o = style && style.offset_2d;
    return [o ? _num(o[0], 0) : fallback[0], o ? _num(o[1], 0) : fallback[1]];
}

export class AxesOverlay {
    constructor(spec) {
        this.spec = spec || {};
        this.svg = null;
        this._root = null;
    }

    mount(container) {
        const svg = document.createElementNS(SVG_NS, 'svg');
        svg.setAttribute('class', 'tanga-axes-overlay');
        svg.style.position = 'absolute';
        svg.style.top = '0';
        svg.style.left = '0';
        svg.style.width = '100%';
        svg.style.height = '100%';
        svg.style.pointerEvents = 'none';
        svg.style.zIndex = '6';
        container.appendChild(svg);
        this.svg = svg;
        this._root = document.createElementNS(SVG_NS, 'g');
        svg.appendChild(this._root);
    }

    setSpec(spec) {
        this.spec = spec || {};
        this._clear();
    }

    dispose() {
        if (this.svg && this.svg.parentNode) this.svg.parentNode.removeChild(this.svg);
        this.svg = null;
        this._root = null;
    }

    _clear() {
        if (this._root) {
            while (this._root.firstChild) this._root.removeChild(this._root.firstChild);
        }
    }

    /**
     * @param {{left:number,right:number,top:number,bottom:number,zoom:number,x:number,y:number}} cameraParams
     * @param {number} width  pane CSS width
     * @param {number} height pane CSS height
     * @param {number} [bottomInset=0]  reserved space at the pane bottom (e.g. annotation)
     */
    update(cameraParams, width, height, bottomInset) {
        if (!this.svg || !this._root) return;
        const spec = this.spec;
        const border = _num(spec.border_px, 0);
        const w = _num(width, 0);
        const h = _num(height, 0);
        const plotH = Math.max(0, h - _num(bottomInset, 0));
        const left = border;
        const top = border;
        const right = w - border;
        const bottom = plotH - border;
        const frameW = Math.max(0, right - left);
        const frameH = Math.max(0, bottom - top);

        this._clear();

        const rect = visibleWorldRect(cameraParams);
        const layout = ticksAndGrid(rect, spec, { width: w, height: plotH });

        const axis = spec.axis || {};
        const xAxis = axis.x || {};
        const yAxis = axis.y || {};
        const xColor = _color(xAxis, '#cccccc');
        const yColor = _color(yAxis, '#cccccc');

        const frameEl = document.createElementNS(SVG_NS, 'rect');
        frameEl.setAttribute('x', left);
        frameEl.setAttribute('y', top);
        frameEl.setAttribute('width', frameW);
        frameEl.setAttribute('height', frameH);
        frameEl.setAttribute('fill', 'none');
        frameEl.setAttribute('stroke', xColor);
        frameEl.setAttribute('stroke-opacity', _num(xAxis.opacity, 0.9));
        frameEl.setAttribute('stroke-width', _num(xAxis.line_thickness, 1));
        this._root.appendChild(frameEl);

        const xValue = xAxis.value_style || {};
        const xOff = _off2d(xValue, [0, 6]);
        for (const [, label, px] of layout.xTicks) {
            this._line(px, bottom, px, bottom + 4, xColor, _num(xAxis.line_thickness, 1));
            this._text(
                label, px + xOff[0], bottom + xOff[1],
                _num(xValue.font_size, 12), _color(xValue, xColor),
                'middle', 'hanging', _num(xValue.rotation, 0),
            );
        }

        const yValue = yAxis.value_style || {};
        const yOff = _off2d(yValue, [-8, 0]);
        for (const [, label, py] of layout.yTicks) {
            this._line(left, py, left - 4, py, yColor, _num(yAxis.line_thickness, 1));
            this._text(
                label, left + yOff[0], py + yOff[1],
                _num(yValue.font_size, 12), _color(yValue, yColor),
                'end', 'middle', _num(yValue.rotation, 0),
            );
        }

        const xLabel = xAxis.label_style || {};
        const yLabel = yAxis.label_style || {};
        const labels = spec.labels || [];
        if (labels[0]) {
            const off = _off2d(xLabel, [0, 28]);
            this._text(
                labels[0], left + frameW / 2 + off[0], bottom + off[1],
                _num(xLabel.font_size, 12), _color(xLabel, xColor),
                'middle', 'hanging', _num(xLabel.rotation, 0), true,
            );
        }
        if (labels[1]) {
            const off = _off2d(yLabel, [-50, 0]);
            this._text(
                labels[1], left + off[0], top + frameH / 2 + off[1],
                _num(yLabel.font_size, 12), _color(yLabel, yColor),
                'middle', 'middle', _num(yLabel.rotation, -90), true,
            );
        }
    }

    _line(x1, y1, x2, y2, color, width) {
        const line = document.createElementNS(SVG_NS, 'line');
        line.setAttribute('x1', x1);
        line.setAttribute('y1', y1);
        line.setAttribute('x2', x2);
        line.setAttribute('y2', y2);
        line.setAttribute('stroke', color);
        line.setAttribute('stroke-width', width);
        this._root.appendChild(line);
    }

    _text(text, x, y, size, color, anchor, baseline, rotation, bold) {
        const t = document.createElementNS(SVG_NS, 'text');
        t.setAttribute('x', x);
        t.setAttribute('y', y);
        t.setAttribute('font-size', size);
        t.setAttribute('fill', color);
        t.setAttribute('text-anchor', anchor);
        t.setAttribute('dominant-baseline', baseline);
        if (bold) t.setAttribute('font-weight', 'bold');
        if (rotation) t.setAttribute('transform', `rotate(${rotation} ${x} ${y})`);
        t.textContent = text;
        this._root.appendChild(t);
    }
}
