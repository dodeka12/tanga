# Phase 1 — Fix `display_static` inline rendering

**Status:** Planned

## Goal

`viz.display_static()` currently returns `IPython.display.HTML(html)` where
`html` is a complete standalone HTML document (from `render_export_html`).
Injected inline, that document's global `<style>` (`html, body { … }`),
`<script type="importmap">`, and `document.body`-targeting bootstrap leak into
the notebook page, paint the whole notebook dark, and can crash the kernel.

Fix it by wrapping the standalone document in an `<iframe srcdoc="…">` so the
document renders in its own isolated browsing context.

## Files

- Modify: `py/pytanga/viz/visualizer.py` (`Visualizer.display_static`, ~line 1791)

## Steps

- [ ] In the `_jupyter` branch of `display_static`, escape the HTML
      (`html.escape(html, quote=True)`) and return
      `HTML(f'<iframe srcdoc="{escaped}" width="{width}" height="{height}" …></iframe>')`.
- [ ] Honor the currently-ignored `width`/`height` parameters (normalize
      `int`/`str` to a CSS value + `px`).
- [ ] Keep the non-Jupyter branch as-is (temp file + `webbrowser.open`), which
      becomes the basis for `open_snapshot()` in Phase 4.

## Unit tests

- [ ] `py/tests/viz/test_display.py` (new):
  - [ ] With `viz._jupyter = True`, `display_static()` returns an
        `IPython.display.HTML` whose `.data` starts with `<iframe srcdoc=`.
  - [ ] The `srcdoc` content is HTML-escaped (`&lt;!DOCTYPE html&gt;`) and does
        not contain a bare `<style>`/`<html>`/`<body>` tag.
  - [ ] With `viz._jupyter = False`, it writes a temp file and returns `None`
        (patch `webbrowser.open`).

## Verification

- [ ] `uv run pytest py/tests/viz/test_display.py` passes.
- [ ] Manual: in a Jupyter notebook, `viz.display_static()` renders inline and
      the rest of the notebook is unaffected.
