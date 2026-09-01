// Tanga Viewer — theme manager.
// Applies the active theme's CSS by managing `<link data-tanga-theme>` tags.
// The server resolves the ordered CSS file list (see `registry.json`) and
// sends it in a `theme_define` message; the browser never parses the JSON.

let _activeTheme = null;

/**
 * Apply a `theme_define` message: replace the existing theme `<link>`s with one
 * per `msg.css` path (in order).  Idempotent per theme.
 */
export function handleThemeDefine(msg) {
    const css = msg.css || [];
    const theme = msg.theme || '';

    if (theme && theme === _activeTheme) return;

    document.querySelectorAll('link[data-tanga-theme]').forEach((el) => el.remove());

    for (const path of css) {
        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.setAttribute('data-tanga-theme', '');
        link.href = 'themes/' + path;
        document.head.appendChild(link);
    }

    _activeTheme = theme;
}
