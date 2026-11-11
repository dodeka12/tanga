# Phase 7 — Changelog, PR prep & final sweep

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Record the work in the branch changelog (with the breaking title change called
out), prepare the PR, and run the full validation sweep.

## Files

- New: `docs/changelog/2026/11/11_feat-theme-tokens-chrome.md`
- Edit (at PR time only): `docs/changelog/index.md`
- Read: `dev/workflows/changelog.md`, `dev/workflows/pull-request.md`

## Steps

- [ ] **7.1 — Branch changelog (`docs/changelog/2026/11/11_feat-theme-tokens-chrome.md`)**
  - File name is `DD_<branch-name>.md` with `/` → `-` (per
    `dev/workflows/changelog.md`); month folder is the branch start date.
  - Get the title value first:
    ```bash
    uv run python tools/last-release.py
    ```
    and write `# Changes since version <printed value>` verbatim (never hardcode
    a version).
  - Sections and bullets (wrap at ~80 columns, `- **Headline** — sentence.`):
    - **New Features**
      - **Themeable spacing and typography tokens** — group header spacing,
        stack gap, log rows and markdown tables are now driven by
        `--tanga-*` tokens declared in `base.css`.
      - **GroupView header control** — `show_header=`, `collapsible=` and
        `title_size=` let a group drop its bar, become static, or re-size its
        title.
      - **Per-instance font sizes** — `LogView(font_size=…)` and
        `MarkdownView(font_size=…)` override the theme for one pane.
      - **Markdown tables are styled** — markdown tables now get borders,
        padding and a header background from the theme.
    - **Breaking Changes**
      - **`GroupView` no longer defaults the title to `"Controls"`** — a
        `title` of `None` or `""` renders no title; pass an explicit title to
        keep the old look.
    - **Bug Fixes**
      - **`compact` theme title override now applies** — it set a token nothing
        consumed.
      - **`StackView`/`GroupView` measure an explicit `gap`** — the gap was
        never passed into the size arithmetic, so a non-default `gap` measured
        wrong.
    - **Refactor**
      - **Group header appearance moved out of JS** — `margin-bottom` / `gap`
        are no longer inlined, so themes can target them.
  - Do **not** add `docs/changelog/index.md` yet — that happens at PR time with
    the squashed hash.

- [ ] **7.2 — PR preparation (follow `dev/workflows/pull-request.md`)**
  - Confirm every phase's `## Validation` passed and the plan's `Status:` line
    in `dev/todos/viz-theme-tokens-chrome/README.md` is `Done`.
  - Check the branch is clean and the plan folder is committed.
  - Summarise the user-visible changes in the PR description: the token list,
    the new kwargs, and the breaking title default (with a migration line:
    `GroupView("Controls", …)`).

- [ ] **7.3 — Full validation sweep**
  - Python: `uv run pytest py/tests/viz -q`
  - Lint/format: `uv run ruff check py && uv run ruff format --check py`
  - JS: `cd js/dev && npm run check && npm test` (or
    `node --test tests/*.test.mjs`)
  - Bundle drift: `uv run python tools/build-viewer-js.py --check` — **expect no
    diff**; the control/view templates are not part of `js/tanga-viewer.js`.
    If it reports a diff, stop and investigate rather than rebuilding blindly.
  - Docs: `uv run python tools/generate-example-docs.py --check &&
    uv run mkdocs build --strict`
  - Manual smoke (not automatable here): run
    `uv run python py/examples/viz/ui/themes/custom_theme_autoreload.py`, edit
    `my_theme/tokens.css` spacing values, confirm the panel re-spaces live.

## Validation

```bash
uv run pytest py/tests/viz -q && uv run ruff check py && uv run ruff format --check py && \
  cd js/dev && npm run check && npm test && cd ../.. && \
  uv run python tools/build-viewer-js.py --check && \
  uv run python tools/generate-example-docs.py --check && uv run mkdocs build --strict
```

## Notes

- If any phase left an architecture change undocumented, fix
  `docs/dev/architecture/viz-theme-system.md` here (it is the doc the
  `create-plan`/`implement-plan` workflows point at).
- The changelog entry is **not** indexed until the squash-rename step of the PR
  workflow.
