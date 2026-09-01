// Tanga Viewer — `GroupView`: a titled `StackView` (panel chrome) that holds
// control views (or any views). Usable as a split pane or a scene overlay
// (anchored by `position`).

import { StackView } from './stack-view.js';
import { stackMainAxis } from './stack-size.js';
import { createIconElement } from '../controls-panel.js';

const HEADER_HEIGHT = 28; // px — approximate title-bar height

export class GroupView extends StackView {
    constructor({
        title = '',
        direction = 'vertical',
        position = null,
        collapsed = false,
        scrollable = false,
        icon = null,
        icon_only = false,
        parent_id = null,
        id = null,
        children = [],
    } = {}) {
        super({ direction, children: [] });
        this.title = title;
        this.position = position;
        this.collapsed = collapsed;
        this.scrollable = scrollable;
        this.icon = icon;
        this.icon_only = icon_only;
        this.parent_id = parent_id;
        this.groupId = id;

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

        if (this.scrollable) {
            this.el.style.overflow = 'hidden';
        }

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

        if (this.scrollable) {
            this._header.style.flexShrink = '0';
        }

        const titleWrap = document.createElement('div');
        titleWrap.className = 'tanga-group-title-wrap';
        Object.assign(titleWrap.style, {
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
        });

        if (this.icon) {
            const icon = createIconElement(this.icon);
            icon.classList.add('tanga-group-icon');
            titleWrap.appendChild(icon);
        }

        if (!this.icon_only) {
            const titleSpan = document.createElement('span');
            titleSpan.className = 'tanga-group-title';
            titleSpan.textContent = this.title || 'Controls';
            titleWrap.appendChild(titleSpan);
        }

        this._header.appendChild(titleWrap);

        const toggleBtn = document.createElement('button');
        toggleBtn.className = 'tanga-group-toggle';
        toggleBtn.title = 'Collapse / Expand';
        Object.assign(toggleBtn.style, {
            background: 'none',
            border: 'none',
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

        const updateFoldIcon = () => {
            toggleBtn.replaceChildren(
                createIconElement(
                    this.collapsed ? 'material:expand_less' : 'material:expand_more'
                )
            );
        };
        updateFoldIcon();

        toggleBtn.addEventListener('click', () => {
            this.collapsed = !this.collapsed;
            this._applyCollapsed();
            updateFoldIcon();
        });
        this._header.appendChild(toggleBtn);
        this.el.appendChild(this._header);

        this._content = document.createElement('div');
        this._content.className = 'tanga-group-content';
        this.el.appendChild(this._content);
        this._applyFlex(); // retarget flex onto the content div
        this._applyScroll(); // scroll the content region below the title bar
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
