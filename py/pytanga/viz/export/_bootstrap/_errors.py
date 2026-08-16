# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass
"""JS generators for CDN load error detection, loading overlay, and user-facing messages."""


def js_loading_overlay_html() -> str:
    """Return a loading overlay ``<div>`` with a pure-CSS spinner.

    Visible immediately on page load — no JavaScript or CDN dependencies.
    Hides when ``window.__tanga_ready`` is set or ``_CDN_CHECK_SCRIPT`` fires.
    """
    return (
        '<div id="tanga-loading" style="'
        "position:fixed;top:0;left:0;right:0;bottom:0;"
        "background:rgba(26,26,46,0.95);z-index:100000;display:flex;"
        "flex-direction:column;align-items:center;justify-content:center;"
        "font-family:sans-serif;color:#ccc;font-size:14px;"
        "transition:opacity 0.3s;"
        '">'
        '<div style="width:32px;height:32px;'
        "border:3px solid rgba(255,255,255,0.2);"
        "border-top:3px solid #fff;border-radius:50%;"
        'animation:tanga-spin 0.8s linear infinite;margin-bottom:12px;">'
        "</div>"
        "Loading 3D Viewer"
        "<style>@keyframes tanga-spin{to{transform:rotate(360deg)}}</style>"
        "</div>"
    )


def _hide_loading_js() -> str:
    """JS snippet that hides the loading overlay (indented for use inside a function body)."""
    return (
        "    var loadingEl = document.getElementById('tanga-loading');\n"
        "    if (loadingEl) {\n"
        "        loadingEl.style.opacity = '0';\n"
        "        setTimeout(function() {\n"
        "            if (loadingEl.parentNode) loadingEl.remove();\n"
        "        }, 300);\n"
        "    }"
    )


def js_cdn_check_script() -> str:
    """Return a non-module ``<script>`` block that checks CDN load status.

    This runs **before** the importmap/module script and monitors whether
    the essential dependencies (Three.js) load successfully.  Optional
    libraries (marked, KaTeX, html2canvas) trigger a warning that fades
    after a few seconds.

    The module script must set ``window.__tanga_ready = true`` as its first
    statement to signal successful loading.
    """
    hide_loading = _hide_loading_js()

    return f"""<script>
(function() {{
    var ESSENTIAL_FAILED = false;
    var OPTIONAL_SEEN = {{}};
    var OPTIONAL_MISSING = [];

    // ── Detect script load errors ──────────────────────────
    window.addEventListener('error', function(e) {{
        var src = (e.target && e.target.src) || '';
        if (!src) {{
            // Module resolution failure (importmap / Three.js import)
            ESSENTIAL_FAILED = true;
        }} else if (/marked/.test(src) && !OPTIONAL_SEEN.marked) {{
            OPTIONAL_SEEN.marked = true;
            OPTIONAL_MISSING.push('marked (Markdown rendering)');
        }} else if (/katex/.test(src) && !OPTIONAL_SEEN.katex) {{
            OPTIONAL_SEEN.katex = true;
            OPTIONAL_MISSING.push('KaTeX (LaTeX math)');
        }} else if (/html2canvas/.test(src) && !OPTIONAL_SEEN.html2canvas) {{
            OPTIONAL_SEEN.html2canvas = true;
            OPTIONAL_MISSING.push('html2canvas (screenshot overlays)');
        }} else if (/three/.test(src)) {{
            ESSENTIAL_FAILED = true;
        }}
    }}, true);

    // ── Poll for __tanga_ready ─────────────────────────────
    var _pollCount = 0;
    var _slowNotice = null;
    var _resultsShown = false;
    function _pollReady() {{
        _pollCount++;
        if (window.__tanga_ready) {{
{hide_loading}
            if (_slowNotice) {{ _slowNotice.remove(); _slowNotice = null; }}
            return;
        }}
        if (ESSENTIAL_FAILED || window.__tanga_cdn_failed) {{
            ESSENTIAL_FAILED = true;
            // A definitive error was caught — show error banner immediately
            if (!_resultsShown) {{ _showError(); }}
        }} else if (_pollCount >= 50 && !_slowNotice) {{
            // 15 seconds with no errors — probably just a slow connection
            _slowNotice = document.createElement('div');
            _slowNotice.style.position = 'fixed';
            _slowNotice.style.top = '0';
            _slowNotice.style.left = '0';
            _slowNotice.style.right = '0';
            _slowNotice.style.zIndex = '99998';
            _slowNotice.style.background = '#cc8800';
            _slowNotice.style.color = '#fff';
            _slowNotice.style.fontFamily = 'sans-serif';
            _slowNotice.style.fontSize = '13px';
            _slowNotice.style.padding = '8px 16px';
            _slowNotice.style.textAlign = 'center';
            _slowNotice.style.lineHeight = '1.5';
            _slowNotice.innerHTML =
                '<strong>Slow connection.</strong> ' +
                'Libraries are still loading. This may take a while on a slow ' +
                'network connection. The viewer will appear once loading completes.';
            document.body.insertBefore(_slowNotice, document.body.firstChild);
        }}
        if (!ESSENTIAL_FAILED) {{
            setTimeout(_pollReady, 300);
        }}
    }}
    setTimeout(_pollReady, 500);

    // ── CDN reachability probe ──────────────────────────────
    // A failed module import (offline / blocked CDN) does not surface a
    // reliable `src` on the `error` event, so probe the CDN directly and
    // flag a definitive network failure for the error banner.
    (function() {{
        var _probeUrl = 'https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.js';
        var _controller = typeof AbortController !== 'undefined' ? new AbortController() : null;
        var _timer = setTimeout(function() {{
            if (_controller) _controller.abort();
        }}, 6000);
        try {{
            fetch(_probeUrl, {{
                method: 'GET',
                mode: 'no-cors',
                cache: 'no-store',
                signal: _controller ? _controller.signal : undefined
            }}).then(function() {{
                clearTimeout(_timer);
            }}).catch(function(err) {{
                clearTimeout(_timer);
                // Ignore the timeout (handled by the "slow connection"
                // notice); only flag a definitive network failure.
                if (!err || err.name !== 'AbortError') {{
                    window.__tanga_cdn_failed = true;
                }}
            }});
        }} catch (_) {{
            clearTimeout(_timer);
            window.__tanga_cdn_failed = true;
        }}
    }})();

    // ── Show error banner when a definitive failure occurred ─
    function _showError() {{
        _resultsShown = true;
{hide_loading}
        if (_slowNotice) {{ _slowNotice.remove(); _slowNotice = null; }}

        if (ESSENTIAL_FAILED) {{
            var banner = document.createElement('div');
            banner.style.position = 'fixed';
            banner.style.top = '0';
            banner.style.left = '0';
            banner.style.right = '0';
            banner.style.zIndex = '99999';
            banner.style.background = '#cc2222';
            banner.style.color = '#fff';
            banner.style.fontFamily = 'sans-serif';
            banner.style.fontSize = '14px';
            banner.style.padding = '12px 20px';
            banner.style.textAlign = 'center';
            banner.style.lineHeight = '1.5';
            banner.innerHTML =
                '<strong>Failed to load Three.js.</strong> ' +
                'The 3D viewer cannot start. Please check your internet connection, ' +
                'firewall, or corporate proxy settings. Three.js loads from CDN ' +
                '(cdn.jsdelivr.net).';
            document.body.insertBefore(banner, document.body.firstChild);
        }}

        if (OPTIONAL_MISSING.length > 0) {{
            var warning = document.createElement('div');
            warning.style.position = 'fixed';
            warning.style.top = ESSENTIAL_FAILED ? '52px' : '0';
            warning.style.left = '0';
            warning.style.right = '0';
            warning.style.zIndex = '99998';
            warning.style.background = '#cc8800';
            warning.style.color = '#fff';
            warning.style.fontFamily = 'sans-serif';
            warning.style.fontSize = '13px';
            warning.style.padding = '8px 16px';
            warning.style.textAlign = 'center';
            warning.style.transition = 'opacity 1s';
            warning.innerHTML =
                '<strong>Optional libraries unavailable:</strong> ' +
                OPTIONAL_MISSING.join(', ') +
                '. Some features will be degraded.';
            document.body.insertBefore(warning, document.body.firstChild);

            // Fade out after 8 seconds
            setTimeout(function() {{
                warning.style.opacity = '0';
                setTimeout(function() {{ if (warning.parentNode) warning.remove(); }}, 1000);
            }}, 8000);
        }}
    }}
}})();
</script>"""
