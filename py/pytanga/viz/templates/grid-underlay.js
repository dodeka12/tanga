// Tanga Viewer — screen-space coordinate grid renderer (underlay layer).
// Draws grid lines behind the (transparent) scene, filled with the theme
// background colour.  DOM + the shared pure math; no `three`.

import { visibleWorldRect, ticksAndGrid } from './axes-overlay-math.js';

const UNDERLAY_NS = 'http://www.w3.org/2000/svg';

function _underlayNum(value, fallback) {
    const n = Number(value);
    return Number.isFinite(n) ? n : fallback;
}

export class GridUnderlay {
    constructor(spec) {
        this.spec = spec || {};
        this.svg = null;
        this._root = null;
    }

    mount(container) {
        const svg = document.createElementNS(UNDERLAY_NS, 'svg');
        svg.setAttribute('class', 'tanga-grid-underlay');
        svg.style.position = 'absolute';
        svg.style.top = '0';
        svg.style.left = '0';
        svg.style.width = '100%';
        svg.style.height = '100%';
        svg.style.pointerEvents = 'none';
        svg.style.zIndex = '0';
        container.appendChild(svg);
        this.svg = svg;
        this._root = document.createElementNS(UNDERLAY_NS, 'g');
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
        const grid = spec.grid || {};
        const w = _underlayNum(width, 0);
        const h = _underlayNum(height, 0);
        const plotH = Math.max(0, h - _underlayNum(bottomInset, 0));

        this._clear();

        const bg = getComputedStyle(document.documentElement)
            .getPropertyValue('--tanga-bg').trim() || 'rgba(0,0,0,0)';
        const bgRect = document.createElementNS(UNDERLAY_NS, 'rect');
        bgRect.setAttribute('x', 0);
        bgRect.setAttribute('y', 0);
        bgRect.setAttribute('width', w);
        bgRect.setAttribute('height', h);
        bgRect.setAttribute('fill', bg);
        this._root.appendChild(bgRect);

        const rect = visibleWorldRect(cameraParams);
        const border = _underlayNum(spec.border_px, 0);
        const left = border;
        const top = border;
        const right = w - border;
        const bottom = plotH - border;

        const layout = ticksAndGrid(rect, spec, { width: w, height: plotH });

        const color = grid.color || '#555555';
        const opacity = _underlayNum(grid.opacity, 0.5);
        const thickness = _underlayNum(grid.line_thickness, 1);

        for (const [, , px] of layout.xTicks) {
            this._line(px, top, px, bottom, color, opacity, thickness);
        }
        for (const [, , py] of layout.yTicks) {
            this._line(left, py, right, py, color, opacity, thickness);
        }
    }

    _line(x1, y1, x2, y2, color, opacity, width) {
        const line = document.createElementNS(UNDERLAY_NS, 'line');
        line.setAttribute('x1', x1);
        line.setAttribute('y1', y1);
        line.setAttribute('x2', x2);
        line.setAttribute('y2', y2);
        line.setAttribute('stroke', color);
        line.setAttribute('stroke-opacity', opacity);
        line.setAttribute('stroke-width', width);
        this._root.appendChild(line);
    }
}
