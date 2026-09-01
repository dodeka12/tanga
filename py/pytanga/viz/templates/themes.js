// Tanga Viewer — theme manager.
// Applies the active theme's CSS by managing `<link data-tanga-theme>` tags.
// The server resolves the ordered CSS file list (see `registry.json`) and
// sends it in a `theme_define` message; the browser never parses the JSON.

let _activeTheme = null;

/**
 * Apply a `theme_define` message: replace the existing theme `<link>`s with one
 * per `msg.css` path (in order) and mark the active theme name on `<html>`.
 * Idempotent per theme.
 */
export function handleThemeDefine(msg) {
    const css = msg.css || [];
    const theme = msg.theme || '';

    if (theme && theme === _activeTheme) return Promise.resolve();

    document.querySelectorAll('link[data-tanga-theme]').forEach((el) => el.remove());

    const links = css.map((path) => {
        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.setAttribute('data-tanga-theme', '');
        link.href = 'themes/' + path;
        document.head.appendChild(link);
        return link;
    });

    // Marker for any theme-scoped selectors
    // (e.g. `html[data-tanga-theme-name="light"] …`).
    document.documentElement.setAttribute('data-tanga-theme-name', theme);

    _activeTheme = theme;

    // Resolve once the new stylesheets finish loading, so callers that read a
    // computed token (e.g. `--tanga-bg`) observe the new theme, not the old one.
    return Promise.all(links.map((link) => new Promise((resolve) => {
        link.addEventListener('load', resolve, { once: true });
        link.addEventListener('error', resolve, { once: true });
        // Cached sheets may not fire `load`; give them a bounded grace period.
        setTimeout(resolve, 500);
    })));
}
