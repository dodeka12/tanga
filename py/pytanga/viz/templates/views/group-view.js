// Tanga Viewer — `GroupView`: a titled `StackView` (panel chrome) that holds
// control views (or any views). Usable as a split pane or a scene overlay
// (anchored by `position`).

import { StackView } from './stack-view.js';
import { stackMainAxis } from './stack-size.js';

const HEADER_HEIGHT = 28; // px — approximate title-bar height

export class GroupView extends StackView {
    constructor({
        title = '',
        direction = 'vertical',
        position = null,
        collapsed = false,
        children = [],
    } = {}) {
        super({ direction, children: [] });
        this.title = title;
        this.position = position;
        this.collapsed = collapsed;

        this.el.classList.add('tanga-group');
        this._setupChrome();

        for (const child of children) this.addChild(child);
    }

    _setupChrome() {
        Object.assign(this.el.style, {
            display: 'flex',
            flexDirection: 'column',
            position: 'relative',
            background: 'rgba(20, 20, 40, 0.92)',
            border: '1px solid rgba(255, 255, 255, 0.12)',
            borderRadius: '6px',
            padding: '8px 12px',
            fontFamily: 'sans-serif',
            fontSize: '13px',
            color: '#ccc',
            boxShadow: '0 4px 16px rgba(0, 0, 0, 0.5)',
        });

        this._header = document.createElement('div');
        this._header.className = 'tanga-group-header';
        Object.assign(this._header.style, {
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: '6px',
            fontWeight: '600',
            fontSize: '14px',
            color: '#ddd',
        });

        const titleSpan = document.createElement('span');
        titleSpan.className = 'tanga-group-title';
        titleSpan.textContent = this.title || 'Controls';
        this._header.appendChild(titleSpan);

        const toggleBtn = document.createElement('button');
        toggleBtn.textContent = '▾';
        toggleBtn.title = 'Collapse / Expand';
        Object.assign(toggleBtn.style, {
            background: 'none',
            border: '1px solid rgba(255,255,255,0.12)',
            borderRadius: '3px',
            color: '#aaa',
            cursor: 'pointer',
            fontSize: '14px',
            width: '22px',
            height: '22px',
            padding: '0',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
        });
        toggleBtn.addEventListener('click', () => {
            this.collapsed = !this.collapsed;
            this._applyCollapsed();
            toggleBtn.textContent = this.collapsed ? '▴' : '▾';
        });
        this._header.appendChild(toggleBtn);
        this.el.appendChild(this._header);

        this._content = document.createElement('div');
        this._content.className = 'tanga-group-content';
        this.el.appendChild(this._content);
        this._applyFlex(); // retarget flex onto the content div
        this._applyCollapsed();
    }

    _applyCollapsed() {
        if (this._content) this._content.style.display = this.collapsed ? 'none' : '';
    }

    // The title bar adds to the content size along the stack axis.
    minSizePx(axis, available) {
        const base = super.minSizePx(axis, available);
        if (this.direction !== 'wrap' && axis === stackMainAxis(this.direction)) {
            return base + HEADER_HEIGHT;
        }
        return base;
    }

    preferredPx(axis, available) {
        const base = super.preferredPx(axis, available);
        if (
            base !== null && base !== undefined &&
            this.direction !== 'wrap' && axis === stackMainAxis(this.direction)
        ) {
            return base + HEADER_HEIGHT;
        }
        return base;
    }
}
