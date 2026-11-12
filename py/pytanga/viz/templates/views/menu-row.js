// Tanga Viewer — DOM-target helpers for menu option rows.
//
// A menu option is wrapped in `.tanga-control-view` > `.tanga-control.tanga-menu-item`.
// Some controls (notably buttons in a `bar`) do not fill that wrapper, so a
// click on the blank part of the option would otherwise not activate it.  These
// helpers let `MenuView` resolve the row an arbitrary click landed in.

// Elements that handle their own activation / input and must not be forwarded
// to the row's primary control.
const INTERACTIVE_SELECTOR = [
    'button',
    'input',
    'select',
    'textarea',
    'a',
    'label',
    '[role="button"]',
    '[role="checkbox"]',
    '[contenteditable="true"]',
].join(', ');

/** True when `target` is an element that handles its own click. */
export function isMenuRowInteractiveTarget(target) {
    return !!(
        target
        && typeof target.closest === 'function'
        && target.closest(INTERACTIVE_SELECTOR)
    );
}

/**
 * Return the `.tanga-menu-item` option row for `target`, or `null`.
 *
 * Besides a click inside the row itself, this also resolves a click on the
 * enclosing `.tanga-control-view` (where a short control leaves blank space).
 */
export function menuRowForTarget(target) {
    if (!target || typeof target.closest !== 'function') return null;
    const item = target.closest('.tanga-menu-item');
    if (item) return item;
    const view = target.closest('.tanga-control-view');
    if (!view || typeof view.querySelector !== 'function') return null;
    return view.querySelector('.tanga-menu-item');
}
