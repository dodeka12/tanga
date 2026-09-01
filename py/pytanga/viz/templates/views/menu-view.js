// Tanga Viewer — `MenuView`: a hamburger dropdown or a permanent bar of options.
// Extends `StackView` so its options stack (dropdown panel) or flow horizontally
// (bar).  Nested `MenuView` children render as sub-menus that open beside the
// parent panel.

import { StackView } from './stack-view.js';
import { createIconElement } from '../controls-panel.js';

const MODES = ['dropdown', 'bar'];
const FONT = 'sans-serif';

export class MenuView extends StackView {
    constructor({
        trigger_icon = null,
        label = '',
        mode = 'dropdown',
        direction = 'vertical',
        position = null,
        children = [],
    } = {}) {
        super({ direction, children: [] });
        if (!MODES.includes(mode)) {
            throw new Error(
                `mode must be one of ${MODES.join(', ')}, got ${JSON.stringify(mode)}`
            );
        }
        this.trigger_icon = trigger_icon;
        this.label = label;
        this.mode = mode;
        this.position = position;
        this._open = false;
        this._subMenus = [];

        this.el.classList.add('tanga-menu', `tanga-menu-${this.mode}`);
        this.el.style.fontFamily = FONT;

        if (this.mode === 'dropdown') {
            this._buildDropdown();
        } else {
            this._buildBar();
        }

        for (const child of children) this.addChild(child);

        // Outside-click / Escape close any open dropdown.
        this._onGlobalPointerDown = (e) => {
            if (!this.el.contains(e.target)) this.close();
        };
        this._onGlobalKeyDown = (e) => {
            if (e.key === 'Escape') this.close();
        };
        document.addEventListener('pointerdown', this._onGlobalPointerDown);
        document.addEventListener('keydown', this._onGlobalKeyDown);
    }

    _buildDropdown() {
        Object.assign(this.el.style, {
            position: 'relative',
            display: 'inline-block',
        });

        this._trigger = document.createElement('button');
        this._trigger.type = 'button';
        this._trigger.className = 'tanga-menu-trigger';
        Object.assign(this._trigger.style, {
            background: 'none',
            border: 'none',
            color: '#ccc',
            cursor: 'pointer',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            padding: '4px 6px',
            fontSize: '14px',
            lineHeight: '1',
        });
        this._trigger.title = this.label || 'Menu';
        if (this.trigger_icon) {
            this._trigger.appendChild(createIconElement(this.trigger_icon));
        }
        if (this.label) {
            const labelEl = document.createElement('span');
            labelEl.className = 'tanga-menu-label';
            labelEl.textContent = this.label;
            this._trigger.appendChild(labelEl);
        }
        this._trigger.addEventListener('click', (e) => {
            e.stopPropagation();
            this.toggle();
        });
        this.el.appendChild(this._trigger);

        this._panel = document.createElement('div');
        this._panel.className = 'tanga-menu-panel';
        Object.assign(this._panel.style, {
            position: 'absolute',
            top: '100%',
            zIndex: '30',
            minWidth: '160px',
            background: 'rgba(20, 20, 40, 0.95)',
            border: '1px solid rgba(255, 255, 255, 0.12)',
            borderRadius: '4px',
            padding: '4px',
            display: 'none',
            flexDirection: this.direction === 'horizontal' ? 'row' : 'column',
            gap: '2px',
        });
        // Right-anchored menus open leftward so the panel stays on-screen.
        if (this.position && this.position.includes('right')) {
            this._panel.style.right = '0';
        } else {
            this._panel.style.left = '0';
        }
        this.el.appendChild(this._panel);
        this._content = this._panel;
    }

    _buildBar() {
        Object.assign(this.el.style, {
            display: 'flex',
            flexDirection: 'row',
            alignItems: 'center',
            gap: '4px',
            background: 'rgba(20, 20, 40, 0.92)',
            border: '1px solid rgba(255, 255, 255, 0.12)',
            borderRadius: '6px',
            padding: '4px 8px',
            boxSizing: 'border-box',
        });
        this._content = this.el;
    }

    open() {
        if (this.mode !== 'dropdown' || this._open) return;
        this._open = true;
        if (this._panel) {
            this._panel.style.display = 'flex';
            if (this._isSubmenu) this._positionSubmenu();
        }
        // Close sibling sub-menus of the same parent.
        if (this._parentMenu) {
            for (const sub of this._parentMenu._subMenus) {
                if (sub !== this) sub.close();
            }
        }
    }

    _positionSubmenu() {
        const panel = this._panel;
        const rect = this.el.getBoundingClientRect();
        const width = panel.offsetWidth || 160;
        if (rect.right + width > window.innerWidth) {
            panel.style.left = 'auto';
            panel.style.right = '100%';
        } else {
            panel.style.right = 'auto';
            panel.style.left = '100%';
        }
        panel.style.top = '0';
    }

    close() {
        this._open = false;
        if (this._panel) this._panel.style.display = 'none';
        for (const sub of this._subMenus) sub.close();
    }

    toggle() {
        if (this._open) this.close();
        else this.open();
    }

    addChild(child) {
        if (child instanceof MenuView) {
            child._parentMenu = this;
            child._isSubmenu = true;
            child.el.classList.add('tanga-menu-sub');
            this._subMenus.push(child);
            child._markSubmenu();
        }
        super.addChild(child);
        return child;
    }

    _markSubmenu() {
        // Widen the trigger and add a chevron so the sub-menu reads as a row.
        if (!this._trigger) return;
        this._trigger.style.width = '100%';
        this._trigger.style.justifyContent = 'space-between';
        if (!this._trigger.querySelector('.tanga-menu-chevron')) {
            const chevron = createIconElement('material:chevron_right');
            chevron.classList.add('tanga-menu-chevron');
            chevron.style.fontSize = '16px';
            this._trigger.appendChild(chevron);
        }
    }

    removeChild(child) {
        if (child instanceof MenuView) {
            const idx = this._subMenus.indexOf(child);
            if (idx !== -1) this._subMenus.splice(idx, 1);
        }
        super.removeChild(child);
    }

    destroy() {
        document.removeEventListener('pointerdown', this._onGlobalPointerDown);
        document.removeEventListener('keydown', this._onGlobalKeyDown);
        super.destroy();
    }
}
