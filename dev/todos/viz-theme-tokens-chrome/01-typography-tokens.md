# Phase 1 — Typography tokens

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

No hardcoded font size remains in the group / log / markdown chrome: each one
becomes a token declared in `base.css`, aliasing the existing type scale, and
the dead `--tanga-font-size-title` becomes live (fixing the `compact` theme,
whose title override currently has no effect).

## Files

- Edit: `py/pytanga/viz/templates/themes/base.css`
- Edit: `py/pytanga/viz/templates/themes/views/group-view.css`
- Edit: `py/pytanga/viz/templates/themes/views/message-view.css`
- Edit: `py/pytanga/viz/templates/themes/views/markdown-view.css`
- Edit: `py/pytanga/viz/templates/themes/compact/tokens.css`
- Edit: `py/tests/viz/test_themes.py`

## Steps

- [ ] **1.1 — Declare the typography tokens (`themes/base.css`)**
  - Insert directly after `--tanga-group-nested-title-size` (`base.css:79`):
    ```css
    /* Component typography (theme-able; aliases of the type scale above). */
    --tanga-group-title-font-size: var(--tanga-font-size-title);
    --tanga-group-body-font-size: var(--tanga-font-size-body);
    --tanga-group-toggle-font-size: 14px;
    --tanga-group-toggle-size: 22px;
    --tanga-font-size-log: var(--tanga-font-size-body);
    --tanga-log-row-padding: 3px 8px;
    --tanga-log-row-gap: 8px;
    --tanga-font-size-markdown: var(--tanga-font-size-body);
    --tanga-markdown-table-cell-padding: 2px 8px;
    ```
  - Comment must state that the `group-title` / `body` / `log` / `markdown`
    values are *aliases*: setting `--tanga-font-size-title` or
    `--tanga-font-size-body` still scales all of them, because custom
    properties resolve per element.

- [ ] **1.2 — Consume them in `themes/views/group-view.css`**
  - `:9` (`.tanga-group`) and `:24` (`.tanga-control-panel`):
    `font-size: var(--tanga-group-body-font-size);`
  - `:53` (`.tanga-group-title`): `font-size: var(--tanga-group-title-font-size);`
  - Replace the nested rule at `:62-66` with the scoped-property indirection so
    a per-instance override (phase 4) can still win:
    ```css
    /* A group nested inside a ParamsView renders a smaller title; it re-scopes
     * the title token so an instance override on the group element still wins. */
    .tanga-group.tanga-group-nested {
        --tanga-group-title-font-size: var(--tanga-group-nested-title-size);
    }
    ```
  - `:78-80` (`.tanga-group-toggle`):
    `font-size: var(--tanga-group-toggle-font-size);`
    `width: var(--tanga-group-toggle-size);`
    `height: var(--tanga-group-toggle-size);`
  - Leave every *other* font size in the sheet (status/footer text at `:104`,
    `:127`, `:157`, `:162`, `:180`, `:185`, `:190`) untouched — out of scope.

- [ ] **1.3 — Consume them in `themes/views/message-view.css`**
  - `.tanga-message-view` (`:3-7`): add
    `font-size: var(--tanga-font-size-log);`
  - `.tanga-message-row` (`:9-15`): `gap: var(--tanga-log-row-gap);` and
    `padding: var(--tanga-log-row-padding);`
  - `.tanga-message-time` keeps `font-family: monospace`.

- [ ] **1.4 — `themes/views/markdown-view.css`: font size + table cells**
  - `.tanga-markdown-body` (`:3-9`): add
    `font-size: var(--tanga-font-size-markdown);`
  - Append the missing table rules (markdown tables are currently unstyled):
    ```css
    .tanga-markdown-body table {
        border-collapse: collapse;
        margin: 0.4em 0;
    }

    .tanga-markdown-body th,
    .tanga-markdown-body td {
        border: 1px solid var(--tanga-border-subtle);
        padding: var(--tanga-markdown-table-cell-padding);
        text-align: left;
    }

    .tanga-markdown-body th {
        background: var(--tanga-surface);
        color: var(--tanga-fg-strong);
    }
    ```

- [ ] **1.5 — Fix the `compact` theme (`themes/compact/tokens.css`)**
  - Replace `--tanga-font-size-title: 13px;` (`:17`) with
    `--tanga-group-title-font-size: 13px;` so the dense variant actually
    shrinks the group title.  Keep the file's existing ordering/grouping style.

- [ ] **1.6 — Token-coverage tests (`py/tests/viz/test_themes.py`)**
  - Reuse `_THEMES_DIR` (already imported) and add a `_theme_css(rel)` helper
    returning `(_THEMES_DIR / rel).read_text(encoding="utf-8")`.
  - Add a parametrised `test_component_token_declared_and_consumed` over these
    pairs (token declared in `base.css` **and** used as `var(--token)` in the
    sheet):
    `--tanga-group-title-font-size` → `views/group-view.css`,
    `--tanga-group-body-font-size` → `views/group-view.css`,
    `--tanga-group-toggle-font-size` → `views/group-view.css`,
    `--tanga-group-toggle-size` → `views/group-view.css`,
    `--tanga-font-size-log` → `views/message-view.css`,
    `--tanga-log-row-padding` → `views/message-view.css`,
    `--tanga-log-row-gap` → `views/message-view.css`,
    `--tanga-font-size-markdown` → `views/markdown-view.css`,
    `--tanga-markdown-table-cell-padding` → `views/markdown-view.css`.
  - Add `test_every_used_token_is_declared`: collect every `var(--tanga-…)` from
    `base.css` + `_COMPONENTS` and assert each name is declared somewhere in
    `base.css`, `tokens.css`, or a `<theme>/tokens.css`.
  - Add `test_type_scale_is_consumed`: `--tanga-font-size-title` and
    `--tanga-font-size-body` are each referenced by at least one sheet (guards
    the dead-token regression).
  - Add `test_markdown_styles_tables`: `views/markdown-view.css` contains a
    `.tanga-markdown-body table` rule.

## Validation

```bash
uv run pytest py/tests/viz/test_themes.py -q
```

## Notes

- `--tanga-group-nested-title-size` stays as-is; it is now consumed by the
  re-scoping rule instead of directly by `.tanga-group-title`.
- Do **not** touch `templates/controls/label.css` / `LabelView.font_size`; that
  control keeps its own per-instance inline `font-size`.
