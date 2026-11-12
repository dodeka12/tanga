# Phase 5 — Per-instance font sizes

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

One log pane or markdown block can use a different font size than the theme
default, without a per-instance stylesheet: `LogView(font_size=…)`,
`MarkdownView(font_size=…)` → `Markdown(font_size=…)`, each applied as a
**scoped inline custom property** (`--tanga-font-size-log` /
`--tanga-font-size-markdown`) on that view's root element.

## Files

- Edit: `py/pytanga/viz/views/log_view.py`
- Edit: `py/pytanga/viz/views/control_views.py`
- Edit: `py/pytanga/viz/_controls.py`
- Edit: `py/pytanga/viz/templates/views/message-view.js`
- Edit: `py/pytanga/viz/templates/views/markdown-view.js`
- Edit: `py/tests/viz/test_views.py`

## Steps

- [x] **5.1 — `LogView(font_size=…)` (`views/log_view.py`)**
  - Keyword-only `font_size: float | None = None` after `show_utc_offset`;
    docstring: "font size in px for this pane only; `None` uses the theme's
    `--tanga-font-size-log`".
  - Validate `font_size <= 0` → `ValueError` (same shape as `max_history`).
  - Store `self.font_size = font_size`.
  - `_serialize()`: `if self.font_size is not None: result["font_size"] =
    self.font_size`.

- [x] **5.2 — `MessageView` applies it (`views/message-view.js`)**
  - Constructor option `font_size = null` → `this.fontSize = font_size;`.
  - Add:
    ```js
    // Instance override: set only the scoped custom property, so the theme's
    // `--tanga-font-size-log` still governs every other log pane.
    _applyFontSize() {
        if (this.fontSize == null) {
            this.el.style.removeProperty('--tanga-font-size-log');
        } else {
            this.el.style.setProperty('--tanga-font-size-log', `${this.fontSize}px`);
        }
    }
    ```
  - Call it from the constructor (after the class list is added) and from
    `update()` via `if ('font_size' in node) this.fontSize = node.font_size ?? null;`
    followed by `_applyFontSize()`.

- [x] **5.3 — `Markdown.font_size` (`_controls.py:1849-1859`)**
  - Add `font_size: float | None = None` to the dataclass and return it from
    `_fields()` only when set:
    ```python
    def _fields(self) -> dict[str, Any]:
        fields: dict[str, Any] = {"value": self.value}
        if self.font_size is not None:
            fields["font_size"] = self.font_size
        return fields
    ```
  - Docstring must note the deliberate difference from `Label.font_size`
    (which defaults to `14`): markdown defaults to `None` so the theme token
    governs unless the caller opts in.

- [x] **5.4 — `MarkdownView(font_size=…)` (`views/control_views.py:806-843`)**
  - Keyword-only `font_size: float | None = None`, validate `<= 0`, pass
    `font_size=font_size` into the `Markdown(...)` control, and expose a
    read-only `font_size` property mirroring `LabelView`'s.

- [x] **5.5 — `MarkdownView` applies it (`views/markdown-view.js`)**
  - `constructor({ id, value = '', font_size = null })` → `this.fontSize`.
  - `update(node)`: `if ('font_size' in node) this.fontSize = node.font_size ?? null;`
    then `this._applyFontSize();`
  - `_applyFontSize()` mirrors 5.2 (property name
    `--tanga-font-size-markdown`, set on `this.el` so the inherited value
    reaches `.tanga-markdown-body`).
  - Call it from `_onMounted()` too, so the first paint already honours it.

- [x] **5.6 — Tests (`py/tests/viz/test_views.py`)**
  - `test_log_view_font_size_serialized_only_when_set` — absent by default,
    `== 16.0` when passed.
  - `test_log_view_font_size_validation` — `font_size=0` raises `ValueError`.
  - `test_markdown_view_font_size` — `MarkdownView("md", value="# x",
    font_size=16).control.font_size == 16.0` and the serialized control node
    carries `"font_size": 16.0`; without the argument the key is absent from
    `_fields()`.
  - `test_markdown_font_size_absent_by_default` — `Markdown(id="md",
    value="x")._fields() == {"value": "x"}`.

## Validation

```bash
uv run pytest py/tests/viz/test_views.py -q
cd js/dev && npm run check
```

## Notes

- Nothing is pushed at runtime: `font_size` is construction-time (a layout
  re-push is what refreshes it), matching the README contract.
- `message-view.js` keeps `this.el.style.overflow = 'auto'` (geometry, allowed
  inline); only the custom property is added.
- `--tanga-font-size-log` / `--tanga-font-size-markdown` must exist in
  `base.css` (phase 1) for the fallback chain to stay meaningful.
