// Tanga Viewer — click-target helpers for group title bars.

// Elements inside a group header that handle their own activation and must not
// also fold the group.
const INTERACTIVE_SELECTOR = [
    'button',
    'a',
    'input',
    'select',
    'textarea',
    '[role="button"]',
].join(', ');

/**
 * True when a header click came from the fold toggle or another interactive
 * descendant.
 *
 * Uses the event's composed path rather than `event.target.closest(...)`.
 * The toggle's own click listener redraws its icon before the event bubbles to
 * the header, which detaches the clicked icon node from the DOM.  At that point
 * `target.closest('.tanga-group-toggle')` returns `null` and the header would
 * treat the same click as a title click, toggling the group straight back.
 * The composed path is captured at dispatch time, so it still contains the
 * toggle button after the icon is replaced.
 */
export function isGroupHeaderInteractiveEvent(event) {
    if (!event) return false;
    const path = typeof event.composedPath === 'function'
        ? event.composedPath()
        : [event.target];
    return path.some((node) => !!(
        node
        && typeof node.closest === 'function'
        && node.closest(INTERACTIVE_SELECTOR)
    ));
}
