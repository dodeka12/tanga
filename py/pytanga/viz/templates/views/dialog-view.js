// Tanga Viewer — `DialogView`: a transient dialog rendered as a `View`.
// A title bar + borderless close ✕ wrap a content container that mounts the
// serialized `content` view subtree (built via `buildViewTree`).  Closing the
// dialog sends `sendEvent(id, "close")` and tears the subtree down.

import { View } from './view.js';
import { buildViewTree } from './build.js';
import { sendEvent } from '../events.js';
import { forgetControl } from '../controls-panel.js';
import { unregisterFileBrowser } from '../file-browser.js';

export class DialogView extends View {
    constructor({
        id,
        title = '',
        content = null,
        align_x = 0.5,
        align_y = 0.5,
        dismissable = true,
        width = null,
        height = null,
        ws = null,
    } = {}) {
        super();
        this.dialogId = id;
        this.title = title;
        this.contentNode = content;
        this.dismissable = dismissable;
        this.ws = ws;
        this._contentView = null;
        this._backdrop = null;
        this._dismissed = false;

        // Keep a dragged (pixel-positioned) dialog inside the viewport when it
        // shrinks; percentage-anchored dialogs stay centered on their own.
        this._onResize = () => this._clampToViewport();
        window.addEventListener('resize', this._onResize);

        this.el.classList.add('tanga-dialog');
        Object.assign(this.el.style, {
            left: (align_x * 100) + '%',
            top: (align_y * 100) + '%',
            transform: 'translate(-' + (align_x * 100) + '%, -' + (align_y * 100) + '%)',
        });

        const widthCss = _sizeToCss(width);
        const heightCss = _sizeToCss(height);
        if (widthCss) this.el.style.width = widthCss;
        if (heightCss) this.el.style.height = heightCss;

        if (!dismissable) {
            this._backdrop = document.createElement('div');
            this._backdrop.className = 'tanga-dialog-backdrop';
        }
    }

    _onMounted() {
        this._buildContent();
        if (this._backdrop) {
            this.el.parentElement.insertBefore(this._backdrop, this.el);
        }
    }

    _buildContent() {
        if (this.title) {
            const title = document.createElement('div');
            title.className = 'tanga-dialog-title';
            title.textContent = this.title;
            this._setupDrag(title);
            this.el.appendChild(title);
        }

        const contentEl = document.createElement('div');
        contentEl.className = 'tanga-dialog-content';
        if (this.contentNode) {
            this._contentView = buildViewTree(this.contentNode, this.ws);
            this._contentView.mount(contentEl);
        }
        this.el.appendChild(contentEl);

        if (this.dismissable) {
            const close = document.createElement('button');
            close.textContent = '✕';
            close.title = 'Dismiss';
            close.className = 'tanga-dialog-close';
            close.addEventListener('click', () => this._dismiss(true));
            this.el.appendChild(close);
        }

        this._setupResize();
    }

    // Resize by dragging the bottom-right corner.  On first move the
    // percentage/transform anchor becomes a pixel position so the dialog stays
    // anchored at its top-left while growing/shrinking.
    _setupResize() {
        this._resizeHandle = document.createElement('div');
        this._resizeHandle.className = 'tanga-dialog-resize';
        this._resizeHandle.title = 'Resize';
        this._resizeHandle.addEventListener('pointerdown', (e) => this._startResize(e));
        this.el.appendChild(this._resizeHandle);
    }

    _startResize(e) {
        if (e.button !== 0) return; // left button only
        e.preventDefault();
        const rect = this.el.getBoundingClientRect();
        const startX = e.clientX;
        const startY = e.clientY;
        const startW = rect.width;
        const startH = rect.height;
        this.el.style.left = rect.left + 'px';
        this.el.style.top = rect.top + 'px';
        this.el.style.transform = 'none';
        const onMove = (ev) => {
            this.el.style.width = Math.max(200, startW + ev.clientX - startX) + 'px';
            this.el.style.height = Math.max(120, startH + ev.clientY - startY) + 'px';
        };
        const onUp = () => {
            window.removeEventListener('pointermove', onMove);
            window.removeEventListener('pointerup', onUp);
        };
        window.addEventListener('pointermove', onMove);
        window.addEventListener('pointerup', onUp);
    }

    // Drag the dialog by its title bar.  On first move the percentage/transform
    // anchor is converted to pixel offsets so subsequent moves are trivial.
    _setupDrag(handle) {
        handle.addEventListener('pointerdown', (e) => {
            if (e.button !== 0) return; // left button only
            e.preventDefault();
            const rect = this.el.getBoundingClientRect();
            const maxLeft = Math.max(0, window.innerWidth - rect.width);
            const maxTop = Math.max(0, window.innerHeight - rect.height);
            this.el.style.left = _clamp(rect.left, 0, maxLeft) + 'px';
            this.el.style.top = _clamp(rect.top, 0, maxTop) + 'px';
            this.el.style.transform = 'none';
            const startX = e.clientX;
            const startY = e.clientY;
            const origLeft = rect.left;
            const origTop = rect.top;
            const onMove = (ev) => {
                this.el.style.left = _clamp(origLeft + ev.clientX - startX, 0, maxLeft) + 'px';
                this.el.style.top = _clamp(origTop + ev.clientY - startY, 0, maxTop) + 'px';
            };
            const onUp = () => {
                window.removeEventListener('pointermove', onMove);
                window.removeEventListener('pointerup', onUp);
            };
            window.addEventListener('pointermove', onMove);
            window.addEventListener('pointerup', onUp);
        });
    }

    // Re-pin a dragged (pixel-positioned) dialog inside the viewport.  A
    // percentage/transform-anchored dialog is centered by CSS, so it is skipped.
    _clampToViewport() {
        if (this.el.style.transform !== 'none') return;
        const rect = this.el.getBoundingClientRect();
        const maxLeft = Math.max(0, window.innerWidth - rect.width);
        const maxTop = Math.max(0, window.innerHeight - rect.height);
        this.el.style.left = _clamp(parseFloat(this.el.style.left) || 0, 0, maxLeft) + 'px';
        this.el.style.top = _clamp(parseFloat(this.el.style.top) || 0, 0, maxTop) + 'px';
    }

    _dismiss(notify) {
        if (this._dismissed) return;
        this._dismissed = true;
        if (notify) sendEvent(this.dialogId, 'close');
        this.destroy();
    }

    destroy() {
        window.removeEventListener('resize', this._onResize);
        if (this._backdrop && this._backdrop.parentElement) {
            this._backdrop.remove();
        }
        this._backdrop = null;
        if (this._contentView) {
            for (const id of _collectControlIds(this._contentView)) {
                forgetControl(id);
                unregisterFileBrowser(id);
            }
            this._contentView.destroy();
            this._contentView = null;
        }
        this.unmount();
        super.destroy();
    }
}

/** Collect every control id in a built view subtree (DFS order). */
function _collectControlIds(view, out = []) {
    if (view.controlId) out.push(view.controlId);
    for (const child of view.children || []) _collectControlIds(child, out);
    return out;
}

function _clamp(value, min, max) {
    return Math.max(min, Math.min(value, max));
}

/** Convert a `{value, unit}` size dict to a CSS length string (or null). */
function _sizeToCss(size) {
    if (!size) return null;
    if (size.unit === '%') return size.value + '%';
    if (size.unit === 'px') return size.value + 'px';
    return null;
}
