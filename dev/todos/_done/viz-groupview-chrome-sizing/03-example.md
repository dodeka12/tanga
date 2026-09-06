# Phase 3 — Example: natural fixed banner

## Goal

Update the `layout_sizing.py` example so the "fixed banner" is fixed at its
natural content height (~content + chrome) instead of an arbitrary 120 px,
removing the large gap below the button.

## Files

- Edit: `py/examples/viz/scenes/layout_sizing.py`
- Edit: `docs/py/examples/viz/scenes/layout_sizing.md` (regenerated)

## Steps

- [x] **3.1 — Use a natural fixed height.**
  - Change `fixed_banner`'s `min_height`/`max_height` from `Size.px(120)` to
    `Size.px(85)` (≈ title bar + button + padding), rename its title from
    `"Fixed banner (120 px)"` to `"Fixed banner"`, and update the comment block
    (lines ~174–178) to say the fixed size matches the pane's natural
    content + chrome.
  - Keep `min == max` (the pane must remain fixed, just at a natural size).

- [x] **3.2 — Regenerate example docs.**
  - Run `uv run python tools/generate-example-docs.py` and confirm
    `docs/py/examples/viz/scenes/layout_sizing.md` updates to match the edited
    source.

## Validation

```powershell
uv run python tools/generate-example-docs.py --check
uv run mkdocs build --strict
```

## Notes

- `85` is the natural height for a single `ButtonView` (control floor 32 px)
  plus the measured chrome (~53 px); it is intentionally "about right", not a
  new library constant.
