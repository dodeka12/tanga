// Tanga Viewer — `BannerView`: a transient banner/dialog rendered as a `View`.
// Text is markdown + KaTeX; options are built from the same control factories
// as `controls-panel.js` (sliders/dropdowns stacked, buttons in a row).

import { View } from './view.js';
import { createSlider, createButton, createDropdown, createTextField, createTextArea, createColorPicker, createCheckbox } from '../controls-panel.js';
import { sendLog } from '../events.js';

export class BannerView extends View {
    constructor({
        id,
        title = '',
        text = '',
        align_x = 0.5,
        align_y = 0.5,
        auto_hide = true,
        dismissable = true,
        controls = [],
        backdropMode = 'fixed',
        onClose = null,
    } = {}) {
        super();
        this.bannerId = id;
        this.title = title;
        this.text = text;
        this.autoHide = auto_hide;
        this.dismissable = dismissable;
        this.controls = controls || [];
        this.onClose = onClose;
        this._backdrop = null;
        this._dismissed = false;

        this.el.classList.add('tanga-banner');
        Object.assign(this.el.style, {
            left: (align_x * 100) + '%',
            top: (align_y * 100) + '%',
            transform: 'translate(-' + (align_x * 100) + '%, -' + (align_y * 100) + '%)',
        });

        if (!dismissable) {
            this._backdrop = document.createElement('div');
            this._backdrop.className = 'tanga-banner-backdrop';
            this._backdrop.style.position = backdropMode;
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
            title.className = 'tanga-banner-title';
            title.textContent = this.title;
            this.el.appendChild(title);
        }

        const body = document.createElement('div');
        body.className = 'tanga-banner-text';
        if (typeof marked !== 'undefined') {
            body.innerHTML = marked.parse(this.text, { breaks: true });
        } else {
            body.textContent = this.text;
        }
        if (typeof renderMathInElement !== 'undefined') {
            try {
                renderMathInElement(body, {
                    delimiters: [
                        { left: '$$', right: '$$', display: true },
                        { left: '$', right: '$', display: false },
                    ],
                    throwOnError: false,
                });
            } catch (e) {
                console.warn('KaTeX banner rendering error:', e);
                sendLog('warn', 'KaTeX banner rendering error', { source: 'banner-view.js', data: { error: String(e) } });
            }
        }
        this.el.appendChild(body);

        if (this.controls.length) {
            const buttonRow = document.createElement('div');
            buttonRow.className = 'tanga-banner-buttons';
            const stack = document.createElement('div');
            stack.className = 'tanga-banner-stack';

            for (const ctrl of this.controls) {
                const el = this._buildControl(ctrl);
                if (!el) continue;
                if (ctrl.kind === 'button') {
                    buttonRow.appendChild(el);
                } else {
                    stack.appendChild(el);
                }
            }
            if (buttonRow.childElementCount) this.el.appendChild(buttonRow);
            if (stack.childElementCount) this.el.appendChild(stack);

            if (this.autoHide) {
                const hide = () => this._dismiss(false);
                buttonRow.addEventListener('click', hide, true);
                buttonRow.addEventListener('change', hide, true);
                stack.addEventListener('click', hide, true);
                stack.addEventListener('change', hide, true);
            }
        }

        if (this.dismissable) {
            const close = document.createElement('button');
            close.textContent = '✕';
            close.title = 'Dismiss';
            close.className = 'tanga-banner-close';
            close.addEventListener('click', () => this._dismiss(true));
            this.el.appendChild(close);
        }
    }

    _buildControl(ctrl) {
        ctrl = { ...ctrl, owner: 'banner' };
        if (ctrl.kind === 'slider') return createSlider(ctrl);
        if (ctrl.kind === 'dropdown') return createDropdown(ctrl);
        if (ctrl.kind === 'button') return createButton(ctrl);
        if (ctrl.kind === 'text') return createTextField(ctrl);
        if (ctrl.kind === 'textarea') return createTextArea(ctrl);
        if (ctrl.kind === 'color') return createColorPicker(ctrl);
        if (ctrl.kind === 'checkbox') return createCheckbox(ctrl);
        return null;
    }

    _dismiss(notify) {
        if (this._dismissed) return;
        this._dismissed = true;
        if (notify && this.onClose) this.onClose(this.bannerId);
        this.unmount();
    }

    unmount() {
        if (this._backdrop && this._backdrop.parentElement) {
            this._backdrop.remove();
        }
        this._backdrop = null;
        super.unmount();
    }

    destroy() {
        this.unmount();
        super.destroy();
    }
}

