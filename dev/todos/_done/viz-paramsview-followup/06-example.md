# Phase 6 — Update `params_view_features.py` example

> **Architecture note — check the developer docs.** Before implementing, follow
> `dev/workflows/example-docs.md` (description + `Keywords:` header, then
> regenerate).  No code/architecture change — this phase exercises the new API.

## Goal

The advanced-features example demonstrates the follow-up features: a captioned
full-width button, a full-width markdown status row, a nested group with its own
`extra_rows`, a dotted `set_value`/`set_visible`, and dotted `event.key` output.

## Files

- **Edit** `py/examples/viz/ui/controls/params_view_features.py`.
- **Regenerate** `docs/py/examples/**` via `tools/generate-example-docs.py`.

## Steps

- [x] **6.1 — button caption + full-width markdown**
  - `RowSpec("detect", ButtonUI(title="Detect rim"), …)` → `ButtonUI(label="Detect rim")`
    (full-width caption); `RowSpec("status", MarkdownUI(title="Status"), …)` →
    `MarkdownUI()` (full-width, no key label).
- [x] **6.2 — nested `extra_rows` + dotted keys**
  - Give the nested `GroupUI` an `extra_rows=[…]` button/status row; add a dotted
    runtime action (e.g. a button calling `set_value("bounds.low", …)` or
    `set_visible("bounds.high", …)`), and show a dotted `event.key` in the shared
    `_on_change` output.
- [x] **6.3 — regenerate example docs**
  - `uv run python tools/generate-example-docs.py` then `--check`.

## Validation

```bash
uv run python tools/generate-example-docs.py --check && uv run ruff check py/examples/viz/ui/controls/params_view_features.py && uv run ty check py/examples/viz/ui/controls/params_view_features.py
```

## Notes

- Keep the example runnable: the dotted-key buttons must reference the
  `ParamsView` created before the handlers (module-level late binding), as the
  existing runtime panel does.
