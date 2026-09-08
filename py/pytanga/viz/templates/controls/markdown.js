// Tanga Viewer — the read-only rendered-markdown DOM factory (marked + KaTeX).

import { registerControl, applyTooltip } from '../controls-panel.js';
import { sendLog } from '../events.js';

function _renderMarkdown(el, text) {
    const src = text == null ? '' : String(text);
    // No `breaks: true` here: it turns the newlines inside a multi-line
    // `$$…$$` display-math block into `<br>`, which splits the two `$$`
    // delimiters into separate text nodes and KaTeX's auto-render can no
    // longer match them (leaving the math as literal source).
    if (typeof marked !== 'undefined') {
        el.innerHTML = marked.parse(src);
    } else {
        el.textContent = src;
    }
    if (typeof renderMathInElement !== 'undefined') {
        try {
            renderMathInElement(el, {
                delimiters: [
                    { left: '$$', right: '$$', display: true },
                    { left: '$', right: '$', display: false },
                ],
                throwOnError: false,
            });
        } catch (e) {
            console.warn('KaTeX markdown rendering error:', e);
            sendLog('warn', 'KaTeX markdown rendering error', { source: 'controls/markdown.js', data: { error: String(e) } });
        }
    }
}

export function createMarkdown(ctrl) {
    const wrapper = document.createElement('div');
    wrapper.className = 'tanga-control tanga-markdown';

    const body = document.createElement('div');
    body.className = 'tanga-markdown-body';
    _renderMarkdown(body, ctrl.value);
    wrapper.appendChild(body);

    registerControl(ctrl.id, {
        owner: ctrl.owner || 'panel',
        kind: 'markdown',
        apply: (value) => _renderMarkdown(body, value),
    });
    applyTooltip(wrapper, ctrl);

    return wrapper;
}
