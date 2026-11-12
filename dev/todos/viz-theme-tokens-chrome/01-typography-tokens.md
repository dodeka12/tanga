# Phase 1 — Typography tokens

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

No hardcoded font size remains in the group / log / markdown chrome: each one
becomes a token declared in `base.css`, aliasing the existing type scale, and
the dead `--tanga-font-size-title` becomes live (fixing the `compact` theme,
whose title override currently has no effect).  The group title also gains a
theme-able background/padding/radius, and the top / `small` / `tiny` variants
become token re-scope rules instead of a one-off `.tanga-group-nested` rule.

## Files

- Edit: `py/pytanga/viz/templates/themes/base.css`
- Edit: `py/pytanga/viz/templates/themes/views/group-view.css`
- Edit: `py/pytanga/viz/templates/themes/views/message-view.css`
- Edit: `py/pytanga/viz/templates/themes/views/markdown-view.css`
- Edit: `py/pytanga/viz/templates/themes/compact/tokens.css`
- Edit: `py/tests/viz/test_themes.py`

## Steps

- [x] **1.1 — Declare the typography + title-surface tokens (`themes/base.css`)**
  - Insert directly after `--tanga-group-nested-title-size` (`base.css:79`):
    ```css
    /* Component typography + title surface (theme-able; the font sizes alias
       the type scale above). */
    --tanga-group-title-font-size: var(--tanga-font-size-title);
    --tanga-group-title-bg: var(--tanga-group-title-bg-base);
    --tanga-group-title-padding: 0;
    --tanga-group-title-radius: 0;
    --tanga-group-body-font-size: var(--tanga-font-size-body);
    --tanga-group-toggle-font-size: 14px;
    --tanga-group-toggle-size: 22px;
    --tanga-font-size-log: var(--tanga-font-size-body);
    --tanga-log-row-padding: 3px 8px;
    --tanga-log-row-gap: 8px;
    --tanga-font-size-markdown: var(--tanga-font-size-body);
    --tanga-markdown-table-cell-padding: 2px 8px;

    /* Group styling variants.  The `*-base` values are the all-variants knobs;
       each variant token defaults to its base, so a theme can move every group
       with one declaration or one level with a variant token.  group-view.css
       re-scopes the generic --tanga-group-* consumers to these knobs. */
    --tanga-group-padding-base: 8px 12px;
    --tanga-group-title-bg-base: transparent;
    --tanga-group-header-padding-base: 0 0 6px;
    --tanga-group-header-margin-bottom-base: 6px;
    --tanga-group-header-gap-base: 6px;

    --tanga-group-small-padding: var(--tanga-group-padding-base);
    --tanga-group-small-title-font-size: var(--tanga-group-nested-title-size);
    --tanga-group-small-title-bg: var(--tanga-group-title-bg-base);
    --tanga-group-small-header-padding: var(--tanga-group-header-padding-base);
    --tanga-group-small-header-margin-bottom: var(--tanga-group-header-margin-bottom-base);
    --tanga-group-small-header-gap: var(--tanga-group-header-gap-base);

    --tanga-group-tiny-padding: var(--tanga-group-padding-base);
    --tanga-group-tiny-title-font-size: var(--tanga-font-size-label);
    --tanga-group-tiny-title-bg: var(--tanga-group-title-bg-base);
    --tanga-group-tiny-header-padding: var(--tanga-group-header-padding-base);
    --tanga-group-tiny-header-margin-bottom: var(--tanga-group-header-margin-bottom-base);
    --tanga-group-tiny-header-gap: var(--tanga-group-header-gap-base);
    ```
  - Comment must state that the `group-title` / `body` / `log` / `markdown`
    values are *aliases*: setting `--tanga-font-size-title` or
    `--tanga-font-size-body` still scales all of them, because custom
    properties resolve per element.  `--tanga-group-nested-title-size` is the
    deprecated alias that feeds the `small` variant, so existing theme
    overrides keep working.
  - The `*-base` tokens avoid a cascade trap: if a variant knob had a literal
    default, it would shadow a theme's generic token on every variant.  With
    the base indirection, setting `--tanga-group-padding-base` (or
    `--tanga-group-title-bg-base`) moves **all** variants, while
    `--tanga-group-small-padding` moves only `small`.  The variant defaults
    reproduce today's look except `tiny`'s title
    (`--tanga-font-size-label`, one step below `small`); the `compact` theme
    tightens them (step 1.5 and phase 2 step 2.8).

- [x] **1.2 — Consume them in `themes/views/group-view.css`**
  - `:9` (`.tanga-group`) and `:24` (`.tanga-control-panel`):
    `font-size: var(--tanga-group-body-font-size);`
  - `:51-55` (`.tanga-group-title`) becomes:
    ```css
    .tanga-group-title {
        font-weight: 600;
        font-size: var(--tanga-group-title-font-size);
        color: var(--tanga-fg-strong);
        background: var(--tanga-group-title-bg);
        padding: var(--tanga-group-title-padding);
        border-radius: var(--tanga-group-title-radius);
    }
    ```
    The three surface properties default to `transparent` / `0` / `0`, so the
    rendered look is unchanged until a theme opts in.  The background is on the
    **title span** (chip around the text), not the full header bar.
  - Replace the nested rule at `:62-66` with the variant indirection:
    ```css
    /* Styling variants re-scope the generic tokens; consumers stay unaware. */
    .tanga-group.tanga-group-small {
        --tanga-group-padding: var(--tanga-group-small-padding);
        --tanga-group-title-font-size: var(--tanga-group-small-title-font-size);
        --tanga-group-title-bg: var(--tanga-group-small-title-bg);
        --tanga-group-header-padding: var(--tanga-group-small-header-padding);
        --tanga-group-header-margin-bottom: var(--tanga-group-small-header-margin-bottom);
        --tanga-group-header-gap: var(--tanga-group-small-header-gap);
    }

    .tanga-group.tanga-group-tiny {
        --tanga-group-padding: var(--tanga-group-tiny-padding);
        --tanga-group-title-font-size: var(--tanga-group-tiny-title-font-size);
        --tanga-group-title-bg: var(--tanga-group-tiny-title-bg);
        --tanga-group-header-padding: var(--tanga-group-tiny-header-padding);
        --tanga-group-header-margin-bottom: var(--tanga-group-tiny-header-margin-bottom);
        --tanga-group-header-gap: var(--tanga-group-tiny-header-gap);
    }
    ```
    An instance override (`--tanga-group-title-font-size` inline on the group
    element, phase 4) still wins over both rules, because inline declarations
    beat the stylesheet's custom-property declaration.
  - Keep `.tanga-group.tanga-group-nested` as a **deprecated alias** for
    `small` (the frontend also toggles the class, phase 4), so existing custom
    theme CSS keeps matching:
    ```css
    /* Deprecated: `tanga-group-nested` is the pre-variant name of `small`. */
    .tanga-group.tanga-group-nested {
        --tanga-group-padding: var(--tanga-group-small-padding);
        --tanga-group-title-font-size: var(--tanga-group-small-title-font-size);
        --tanga-group-title-bg: var(--tanga-group-small-title-bg);
        --tanga-group-header-padding: var(--tanga-group-small-header-padding);
        --tanga-group-header-margin-bottom: var(--tanga-group-small-header-margin-bottom);
        --tanga-group-header-gap: var(--tanga-group-small-header-gap);
    }
    ```
  - `:78-80` (`.tanga-group-toggle`):
    `font-size: var(--tanga-group-toggle-font-size);`
    `width: var(--tanga-group-toggle-size);`
    `height: var(--tanga-group-toggle-size);`
  - Leave every *other* font size in the sheet (status/footer text at `:104`,
    `:127`, `:157`, `:162`, `:180`, `:185`, `:190`) untouched — out of scope.

- [x] **1.3 — Consume them in `themes/views/message-view.css`**
  - `.tanga-message-view` (`:3-7`): add
    `font-size: var(--tanga-font-size-log);`
  - `.tanga-message-row` (`:9-15`): `gap: var(--tanga-log-row-gap);` and
    `padding: var(--tanga-log-row-padding);`
  - `.tanga-message-time` keeps `font-family: monospace`.

- [x] **1.4 — `themes/views/markdown-view.css`: font size + table cells**
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

- [x] **1.5 — Fix the `compact` theme (`themes/compact/tokens.css`)**
  - Replace `--tanga-font-size-title: 13px;` (`:17`) with
    `--tanga-group-title-font-size: 13px;` so the dense variant actually
    shrinks the group title.
  - Add the variant title sizes right below it:
    ```css
    --tanga-group-small-title-font-size: 12px;
    --tanga-group-tiny-title-font-size: 11px;
    ```
  - Keep the file's existing ordering/grouping style; the spacing overrides
    for the new tokens are added in phase 2 (step 2.8).

- [x] **1.6 — Token-coverage tests (`py/tests/viz/test_themes.py`)**
  - Reuse `_THEMES_DIR` (already imported) and add a `_theme_css(rel)` helper
    returning `(_THEMES_DIR / rel).read_text(encoding="utf-8")`.
  - Add a parametrised `test_component_token_declared_and_consumed` over these
    pairs (token declared in `base.css` **and** used as `var(--token)` in the
    sheet):
    `--tanga-group-title-font-size` → `views/group-view.css`,
    `--tanga-group-title-bg` → `views/group-view.css`,
    `--tanga-group-title-padding` → `views/group-view.css`,
    `--tanga-group-title-radius` → `views/group-view.css`,
    `--tanga-group-body-font-size` → `views/group-view.css`,
    `--tanga-group-toggle-font-size` → `views/group-view.css`,
    `--tanga-group-toggle-size` → `views/group-view.css`,
    `--tanga-group-small-padding` → `views/group-view.css`,
    `--tanga-group-small-title-font-size` → `views/group-view.css`,
    `--tanga-group-small-title-bg` → `views/group-view.css`,
    `--tanga-group-small-header-padding` → `views/group-view.css`,
    `--tanga-group-small-header-margin-bottom` → `views/group-view.css`,
    `--tanga-group-small-header-gap` → `views/group-view.css`,
    `--tanga-group-tiny-padding` → `views/group-view.css`,
    `--tanga-group-tiny-title-font-size` → `views/group-view.css`,
    `--tanga-group-tiny-title-bg` → `views/group-view.css`,
    `--tanga-group-tiny-header-padding` → `views/group-view.css`,
    `--tanga-group-tiny-header-margin-bottom` → `views/group-view.css`,
    `--tanga-group-tiny-header-gap` → `views/group-view.css`,
    `--tanga-font-size-log` → `views/message-view.css`,
    `--tanga-log-row-padding` → `views/message-view.css`,
    `--tanga-log-row-gap` → `views/message-view.css`,
    `--tanga-font-size-markdown` → `views/markdown-view.css`,
    `--tanga-markdown-table-cell-padding` → `views/markdown-view.css`.
  - Add `test_group_variant_rules_rescope_tokens`: `views/group-view.css`
    contains `.tanga-group.tanga-group-small` and `.tanga-group.tanga-group-tiny`,
    each re-scoping `--tanga-group-padding`,
    `--tanga-group-title-font-size`, `--tanga-group-title-bg` and
    `--tanga-group-header-padding`; the deprecated
    `.tanga-group.tanga-group-nested` rule still exists and points at the
    `small` knobs.
  - Add `test_compact_theme_targets_variant_titles`: `compact/tokens.css` sets
    `--tanga-group-title-font-size`,
    `--tanga-group-small-title-font-size` and
    `--tanga-group-tiny-title-font-size`.
  - Add `test_group_base_tokens_feed_all_variants`: `base.css` declares
    `--tanga-group-padding-base`, `--tanga-group-title-bg-base`,
    `--tanga-group-header-padding-base`,
    `--tanga-group-header-margin-bottom-base` and
    `--tanga-group-header-gap-base`, and the `small`/`tiny` knobs each default
    to the matching base token.
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

- `--tanga-group-nested-title-size` stays declared and now feeds
  `--tanga-group-small-title-font-size`; it is no longer consumed directly by
  `.tanga-group-title`.  Treat it as deprecated in the docs (phase 6).
- The variant rules are pure re-scopes: no selector repeats a concrete value.
  Each `--tanga-group-<level>-*` knob defaults to its shared `*-base` token, so
  a theme moves all variants with `--tanga-group-padding-base` /
  `--tanga-group-title-bg-base` / `--tanga-group-header-*-base`, or one level
  with `--tanga-group-small-*` / `--tanga-group-tiny-*`.
- The plain `--tanga-group-padding` / `--tanga-group-title-bg` /
  `--tanga-group-header-*` tokens are the default-variant **consumers**; a theme
  that sets only those changes top-level groups, not `small`/`tiny`.  This is
  intentional and documented (use the `*-base` token for "all groups").
- Do **not** touch `templates/controls/label.css` / `LabelView.font_size`; that
  control keeps its own per-instance inline `font-size`.
