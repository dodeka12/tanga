# Phase 6 — Docs & example

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Document the new tokens, the group styling variants, the computed-gap sizing
contract, the scoped custom-property instance overrides, the new
`GroupView`/`LogView`/`MarkdownView` options, the header click-to-fold and the
`ParamsView` row-title tooltips — with a runnable example a theme author can
copy, plus a Dark/Compact theme menu in `all_controls.py`.

## Files

- Edit: `docs/py/viz/ui/custom-themes.md`
- Edit: `docs/py/viz/ui/control-views.md`
- Edit: `docs/py/viz/ui/display-views.md`
- Edit: `docs/dev/architecture/viz-theme-system.md`
- Edit: `docs/dev/architecture/viz-controls-and-interactions.md`
- Edit: `py/examples/viz/ui/themes/my_theme/tokens.css`
- Edit: `py/examples/viz/ui/themes/custom_theme_override.py`
- Edit: `py/examples/viz/ui/controls/all_controls.py`
- Regenerated: `docs/py/examples/**` (via `tools/generate-example-docs.py`)

## Steps

- [x] **6.1 — `docs/py/viz/ui/custom-themes.md`: theming spacing & typography**
  - Extend the token table(s) with the phase-1/2 tokens:
    `--tanga-group-padding-base`, `--tanga-group-title-bg-base`,
    `--tanga-group-header-padding-base`,
    `--tanga-group-header-margin-bottom-base`,
    `--tanga-group-header-gap-base`,
    `--tanga-group-padding`, `--tanga-group-title-font-size`,
    `--tanga-group-title-bg`, `--tanga-group-title-padding`,
    `--tanga-group-title-radius`, `--tanga-group-body-font-size`,
    `--tanga-group-toggle-font-size`, `--tanga-group-toggle-size`,
    `--tanga-group-header-padding`, `--tanga-group-header-margin-bottom`,
    `--tanga-group-header-gap`, `--tanga-stack-gap`, `--tanga-font-size-log`,
    `--tanga-log-row-padding`, `--tanga-log-row-gap`,
    `--tanga-font-size-markdown`, `--tanga-markdown-table-cell-padding` — each
    with its default and the sheet that consumes it.
  - Explain the two-tier knobs: the `*-base` tokens move **all** variants; the
    `small`/`tiny` knobs move one level; the plain `--tanga-group-*` tokens are
    the default-variant consumers.
  - Add a per-variant sub-table for the `small` / `tiny` knobs:
    `--tanga-group-{small,tiny}-padding`,
    `--tanga-group-{small,tiny}-title-font-size`,
    `--tanga-group-{small,tiny}-title-bg`, and
    `--tanga-group-{small,tiny}-header-{padding,margin-bottom,gap}`.
    State that the variants default to today's rendering (except `tiny`, one
    step smaller) and that `--tanga-group-nested-title-size` is the deprecated
    alias feeding the `small` title size.
  - Add a worked snippet ("denser panels, roomier log"):
    ```css
    :root {
        --tanga-stack-gap: 2px;
        --tanga-group-padding-base: 6px 8px;
        --tanga-group-header-padding-base: 0 0 4px;
        --tanga-group-header-margin-bottom-base: 4px;
        --tanga-group-title-font-size: 13px;
        --tanga-group-title-bg-base: var(--tanga-surface);
        --tanga-group-title-padding: 1px 6px;
        --tanga-group-title-radius: 3px;
        --tanga-group-small-padding: 4px 6px;
        --tanga-group-small-title-font-size: 12px;
        --tanga-group-tiny-padding: 3px 5px;
        --tanga-group-tiny-title-font-size: 11px;
        --tanga-group-body-font-size: 12px;
        --tanga-font-size-log: 12px;
        --tanga-log-row-padding: 1px 6px;
    }
    ```
    Explain that the title background is painted on the title **text**
    (`.tanga-group-title`), so it needs `title-padding` / `title-radius` to
    look like a chip; a full-width header bar is not a token.
  - State that `--tanga-group-title-font-size` etc. **alias** the type scale, so
    setting `--tanga-font-size-title` / `--tanga-font-size-body` still scales
    everything.
  - Add `### Group variants` — `GroupView(variant=EGroupVariant.SMALL)` /
    `"tiny"`, the three class names (`tanga-group-small`, `-tiny`, and the
    deprecated `tanga-group-nested` alias), and the fact that `ParamsView`
    assigns `small` to its depth-0 field groups and `tiny` deeper.  A bare
    `ParamsView` has no group chrome — wrap it in `GroupView(variant=…)` for the
    top-level panel.  Explicitly: the space **around** a group is the parent
    gap, the space **inside** it is `--tanga-group-padding` (there is no group
    margin token).
  - Add `### Per-instance overrides` — `GroupView(title_size=…)`,
    `LogView(font_size=…)`, `MarkdownView(font_size=…)`, and explain they set a
    scoped CSS custom property on that view only, so the rest of the UI keeps
    following the theme.
  - Add `### Headerless and static groups` — `GroupView(title=None)` /
    `title=""` (no title text), `show_header=False` (no bar), `collapsible=False`
    (no fold toggle); note `show_header=False` keeps the panel padding/border
    and that a collapsible header folds on a click anywhere on the bar.
  - Add `### Dense params vs. the theme` — `.tanga-params-dense` wins over the
    theme tokens by specificity, so `ParamsView(dense=True)` stays dense
    regardless of theme; use the tokens for global density, `dense=True` for a
    single view.
  - Add `### Live theme edits` — `register_theme(…)` + `refresh_theme()` +
    `enable_theme_auto_reload()`, noting theme files are served with
    `Cache-Control: no-cache` and swapped links carry `?v=` so an edit lands on
    the next reload.

- [x] **6.2 — `docs/py/viz/ui/control-views.md`**
  - Update the `GroupView` parameter list: `title: str | None = ""`,
    `show_header: bool = True`, `collapsible: bool = True`,
    `title_size: float | None = None`,
    `variant: EGroupVariant | str = EGroupVariant.DEFAULT`, and
    `set_title(str | None)`.
  - Document `EGroupVariant` (`DEFAULT` / `SMALL` / `TINY`) with a short table
    of what each variant changes (padding, title font/background, header
    spacing) and the explicit note that it is presentational only.
  - Add a paragraph on **header click-to-fold**: a collapsible group folds when
    the header (title area) is clicked; the toggle button still works and is
    never double-fired; `collapsible=False` headers ignore clicks.
  - Add the `GroupUI(variant=…)` / `ParamsView` relationship: field groups are
    `small`, deeper groups `tiny`, `GroupUI.variant` overrides one field.
    Update the existing nested-dataclass sentence (`control-views.md:586`,
    `GroupUI(title=…, collapsed=…, extra_rows=[…])`) to include `variant=…`.
  - Add a `### Row tooltips` note: a value row's key label shows the control's
    `tooltip` (or the dataclass `description` metadata); the page-wide
    `set_tooltips_enabled` switch applies.
  - Add a `!!! warning` note: an empty/`None` title no longer falls back to
    `"Controls"` — pass an explicit title to keep it.
  - Add `MarkdownView(font_size=…)` to its parameter list.

- [x] **6.3 — `docs/py/viz/ui/display-views.md`**
  - `LogView(font_size=…)` documented next to `show_date` / `show_utc_offset`,
    including "`None` (default) follows the theme's `--tanga-font-size-log`".

- [x] **6.4 — Developer architecture docs** (architecture update)
  - `docs/dev/architecture/viz-theme-system.md`:
    - Extend the "Density & typography tokens" list with the new component
      tokens (group padding, title surface, variant knobs) and their consuming
      sheets; mention that the `compact` theme now overrides
      `--tanga-group-title-font-size` **and** the `small`/`tiny` variants.
    - In "Stable class-name contract", document `tanga-group-small` /
      `tanga-group-tiny` as the variant classes, with `tanga-group-nested` as a
      deprecated alias for `small`, and state that the variant only re-scopes
      `--tanga-group-*` tokens.  Mark `--tanga-group-nested-title-size` as the
      deprecated token feeding `--tanga-group-small-title-font-size`.
    - Extend the inline-style sentence: computed geometry **plus scoped
      instance custom properties** (decision B) are the only inline writes; a
      per-instance font size never writes a resolved `font-size`.
    - Add a paragraph for decision A: `StackView`/`GroupView` read the
      *computed* gap (`_gapPx()` → `stackMinSize`/`stackPreferredSize`) so
      `--tanga-stack-gap` moves the layout and the measured size together; an
      explicit Python `gap` wins.  Note the cache invalidation triggers
      (`_applyFlex`, `mount`, `tanga:themechange`).
    - Update the `GroupView` chrome description: a header exists only when
      `show_header and (collapsible or title or icon)`; `title=None`/`""` render
      no title (no `"Controls"` fallback); a collapsible header folds on click;
      `_chromeY()` returns `{folded: 0, chrome: <shell>}` when there is no
      header.
    - Document the `ParamsView` depth rule (`small` at depth 0, `tiny` deeper,
      `GroupUI.variant` override) and that row key labels now carry the
      control's tooltip.
  - `docs/dev/architecture/viz-controls-and-interactions.md:374`: replace the
    `tanga-group-nested` mention with the variant classes and note that the
    group header click delegates to the existing `setCollapsed()` /
    `control:group_toggle` path (no second interaction registry entry for the
    title).

- [x] **6.5 — Example theme tokens (`my_theme/tokens.css`)**
  - Append a commented block so editing it visibly re-spaces the UI (this is the
    folder `custom_theme_autoreload.py` watches):
    ```css
    /* Spacing & typography — edit + save to see the reload. */
    --tanga-stack-gap: 2px;
    --tanga-group-padding-base: 6px 8px;
    --tanga-group-header-padding-base: 0 0 4px;
    --tanga-group-header-margin-bottom-base: 4px;
    --tanga-group-title-font-size: 13px;
    --tanga-group-title-bg-base: var(--tanga-surface);
    --tanga-group-title-padding: 1px 6px;
    --tanga-group-title-radius: 3px;
    --tanga-group-small-padding: 4px 6px;
    --tanga-group-small-title-font-size: 12px;
    --tanga-group-tiny-padding: 3px 5px;
    --tanga-group-tiny-title-font-size: 11px;
    --tanga-group-body-font-size: 12px;
    --tanga-font-size-log: 12px;
    --tanga-log-row-padding: 1px 6px;
    --tanga-markdown-table-cell-padding: 1px 6px;
    ```

- [x] **6.6 — Example (`py/examples/viz/ui/themes/custom_theme_override.py`)**
  - Give the existing `GroupView("Themes", …)` a `title_size=14`.
  - Add a nested `GroupView("Nested", […], variant=EGroupVariant.TINY)` (import
    the enum from `pytanga.viz`) so the variant tokens are visible next to the
    top panel.  Keep it collapsible so the header click is demonstrable.
  - Add a `MarkdownView("notes", value=…, font_size=14)` inside that group whose
    markdown contains a heading, a bullet list and a 2×2 **table**, so the new
    markdown tokens and table CSS are visible in one pane.
  - Update the module docstring's first line/explanation and the `Keywords:`
    line (3–8 task-oriented terms, e.g.
    `theme, custom theme, tokens, spacing, typography, markdown, table`).

- [x] **6.7 — `all_controls` example: `ParamsView` + theme menu**
  - Edit `py/examples/viz/ui/controls/all_controls.py`.
  - Imports: add `EGroupVariant`, `GroupUI`, `ParamsView`, `SliderUI`,
    `DropdownUI` (all exported from `pytanga.viz`) next to the existing imports
    (and `Any` from `typing` if `on_params` annotates its state argument).
  - In `_setup_controls()`, build a `ParamsView`:
    ```python
    params_view = ParamsView(
        {
            "radius": self._radius,
            "mode": "Solid",
            "shape": {"detail": 24, "smooth": True},
        },
        styles={
            "radius": SliderUI(
                min=0.3, max=3.0, step=0.05, tooltip="Scale the sphere"
            ),
            "mode": DropdownUI(
                options=["Solid", "Translucent", "Hidden"],
                tooltip="Switch the material",
            ),
            "shape": GroupUI(
                title="Shape",
                variant=EGroupVariant.TINY,
                tooltip="Nested shape settings",
            ),
        },
        on_change=self.on_params,
    )
    ```
    No `title=` or `tooltip=` — `ParamsView` only takes `View` size kwargs, and
    the enclosing `GroupView` provides the title and the panel tooltip.  The
    `radius` / `mode` row titles get their tooltips from their `ControlUI`s;
    the `shape` `GroupUI.tooltip` lands on the sub-panel header (a group row has
    no key label).
    `shape` is a dict, so `GroupUI` makes `_build_group` create a nested
    `ParamsView` around it; its `variant=TINY` overrides the depth-0 `small`
    default.
  - Add the handler:
    ```python
    async def on_params(self, _state, event: ControlEvent) -> None:
        if event.key == "radius":
            self._apply_radius(float(event.value))
        elif event.key == "mode":
            opacity = {"Solid": 0.9, "Translucent": 0.35, "Hidden": 0.0}
            self.viz.update("ball", opacity=opacity[str(event.value)])
            self.viz.flush()
        self._set_annotation(f"ParamsView: {event.key} = {event.value}")
    ```
  - Add a fourth overlay (the only free anchor) inside the `SceneView`:
    ```python
    GroupView(
        "Parameters",
        [params_view],
        icon=EIconMaterial.TUNE,
        tooltip="A ParamsView with a nested group (variant=TINY)",
        position="bottom-left",
    )
    ```
  - Add a second menu to the existing `MenuView(mode="bar", children=[…])`
    (next to `Help`):
    ```python
    MenuView(
        "Theme",
        [
            ButtonView(
                "theme_dark", label="Dark", tooltip="Dark theme",
                on_click=self.on_theme_dark,
            ),
            ButtonView(
                "theme_compact", label="Compact", tooltip="Compact dense theme",
                on_click=self.on_theme_compact,
            ),
        ],
        trigger_icon=EIconMaterial.PALETTE,
        tooltip="Switch the whole UI theme",
    )
    ```
    with
    ```python
    async def on_theme_dark(self, _value: None, _event: ControlEvent) -> None:
        self.viz.set_theme("dark")
        self._set_annotation("Theme: Dark")

    async def on_theme_compact(self, _value: None, _event: ControlEvent) -> None:
        self.viz.set_theme("compact")
        self._set_annotation("Theme: Compact")
    ```
    `set_theme()` swaps CSS only — no layout re-push, and the `ParamsView`
    keeps its state.  Use `list_themes()` only if the menu is generated
    dynamically; two explicit buttons keep the example readable.
  - Update the module docstring (mention the `ParamsView` sub-group, the group
    variant, click-to-fold and the Dark/Compact menu) and the `Keywords:` line
    with 3–8 task-oriented terms, e.g.
    `params view, nested group, theme, variant, header, tooltip`.
  - Manual check: the Parameters panel shows `radius` / `mode` rows plus a
    `Shape` sub-group that is visibly smaller; clicking any group header folds
    it; the Theme menu switches Dark ↔ Compact; hovering a Parameters row label
    shows its tooltip.

- [x] **6.8 — Regenerate the example docs**
  ```bash
  uv run python tools/generate-example-docs.py
  ```

## Validation

```bash
uv run python tools/generate-example-docs.py --check && uv run mkdocs build --strict
```

## Notes

- `mkdocs build --strict` is the docs gate: a broken relative link or a missing
  nav entry fails it.
- Keep each docs page's existing tone (second person, short code blocks); do not
  restructure `custom-themes.md` beyond adding the new sections.
- `custom_theme_override.py` uses the **built-in** `pastel` theme (it does not
  call `register_theme`); the spacing tokens are demonstrated by
  `my_theme/tokens.css` + `custom_theme_autoreload.py`, not by that example.
  `all_controls.py` switches between the built-in `dark` and `compact` themes
  via `set_theme()` — it is the variant/ParamsView showcase, not a custom-theme
  registration example.
- Both edited examples need their docstring first line and `Keywords:` header
  updated **before** running `generate-example-docs.py` (see
  `dev/workflows/example-docs.md`); the generated pages under
  `docs/py/examples/` are committed.
