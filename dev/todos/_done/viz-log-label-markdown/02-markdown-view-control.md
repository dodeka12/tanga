# Phase 2 — `MarkdownView` display control

## Goal

Deliver `MarkdownView` — a non-editable, settable, multi-line rendered-markdown
control (`value`) with KaTeX math, updated live through `control_update`.

## Files

- Edit: `py/pytanga/viz/_controls.py`
- Edit: `py/pytanga/viz/views.py`
- Edit: `py/pytanga/viz/__init__.py`
- Edit: `py/pytanga/viz/templates/controls-panel.js`
- New: `py/pytanga/viz/templates/views/markdown-view.js`
- Edit: `py/pytanga/viz/templates/views/build.js`
- New: `py/pytanga/viz/templates/themes/views/markdown-view.css`
- Edit: `py/pytanga/viz/templates/themes/registry.json`
- Edit: `py/tests/viz/test_themes.py`, `py/tests/viz/test_views.py`, `py/tests/viz/test_controls.py`

## Steps

- [x] **2.1 — Backend `Markdown` control (`_controls.py`)**
  - Add `@dataclass class Markdown(Control)` with `kind: str = "markdown"`,
    `value: str = ""`.
  - Add a `Markdown` branch to `_serialize_one_control` (`{"value": ctrl.value}`).
  - Add `Markdown` to `get_control_value` (return `ctrl.value`) and
    `set_control_value` (`ctrl.value = str(value)`).

- [x] **2.2 — Backend `MarkdownView` + export**
  - `views.py`: add `MarkdownView(ControlView)` with
    `_node_type = "markdown_view"`, constructor `(cid, *, value="", **kwargs)`
    setting `self.control = Markdown(id=cid, value=value)`.
  - Add `MarkdownView` to `views.py __all__`; import/export it in `__init__.py`
    (do **not** re-export the `Markdown` control).

- [x] **2.3 — Frontend `createMarkdown` (`controls-panel.js`)**
  - Add a `_renderMarkdown(el, text)` helper (marked + KaTeX + fallback) and
    `export function createMarkdown(ctrl)` that builds a
    `<div class="tanga-control tanga-markdown">` with a body element, renders
    `ctrl.value` through the helper, and registers `_controlRegistry[ctrl.id] =
    { owner, kind: 'markdown', apply: (v) => _renderMarkdown(body, v) }`.
  - Helper: `if (typeof marked !== 'undefined') body.innerHTML =
    marked.parse(text, {breaks:true}); else body.textContent = text;` then, if
    `typeof renderMathInElement !== 'undefined'`, call it with `$…$`/`$$…$$`
    delimiters and `throwOnError: false` (same as `banner-view.js`).

- [x] **2.4 — Frontend `MarkdownView` + `build.js`**
  - New `views/markdown-view.js`: `MarkdownView extends ControlView`,
    constructor `{ id, value = '' }`, `render()` → `createMarkdown({ id,
    owner: 'layout', value })`.
  - `build.js`: import `MarkdownView`, add `node.type === 'markdown_view'`
    branch from `node.id`/`node.value`.

- [x] **2.5 — Theme CSS**
  - New `themes/views/markdown-view.css` (base typography for headings, code,
    lists, links, blockquote; scrollable body).
  - Add `"views/markdown-view.css"` to `registry.json` `components` and
    `test_themes.py::_COMPONENTS`.

- [x] **2.6 — Tests**
  - `test_views.py`: `MarkdownView` serializes `type == "markdown_view"` and
    `value`.
  - `test_controls.py`: `get/set_control_value` for `Markdown` (str coercion).

## Validation

```
uv run pytest py/tests/viz/test_views.py py/tests/viz/test_controls.py py/tests/viz/test_themes.py -q
node --check py/pytanga/viz/templates/controls-panel.js py/pytanga/viz/templates/views/markdown-view.js py/pytanga/viz/templates/views/build.js
node --test 'dev/src/js-tests/*.test.mjs'
```

## Notes

- Do **not** refactor `banner-view.js`/`three-view.js` to use the new helper —
  out of scope for this phase.
- `marked` does not render math; KaTeX is a separate post-process step
  (`renderMathInElement`), combined exactly as in `banner-view.js`.
