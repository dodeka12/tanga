# Phase 3 — `copy_theme` scaffold

## Goal

Provide `copy_theme(theme_id, dest_dir)` that copies a theme's own
`tokens.css` + `overrides/` into a local folder, giving users a ready starting
point for a custom theme (they then register it with `register_theme`).

## Files

- Edit: `py/pytanga/viz/_themes.py`
- Edit: `py/pytanga/viz/__init__.py` (export `copy_theme`)
- Edit: `py/tests/viz/test_themes.py`

## Steps

- [ ] **3.1 — `copy_theme` implementation**
  - Add `copy_theme(theme_id, dest_dir, *, overwrite=False) -> Path`:
    - resolve `theme_id` (bundled or registered external);
    - create `dest_dir` if missing;
    - copy the theme's `tokens.css` and its `overrides/` files (preserving
      subpaths), not `base.css`/`components`;
    - refuse to overwrite existing files unless `overwrite=True`;
    - return the destination `Path`.
  - Document that `"pastel"` is the recommended source (full token sheet +
    button/checkbox overrides).

- [ ] **3.2 — Exports**
  - Export `copy_theme` from `py/pytanga/viz/__init__.py` (`__all__`).

- [ ] **3.3 — Tests (`test_themes.py`)**
  - `copy_theme("pastel", tmp_path/"mine")` copies `tokens.css` and the
    `overrides/` files.
  - Re-copying without `overwrite=True` raises; with `overwrite=True` succeeds.
  - The result registers cleanly via `register_theme` and resolves.

## Validation

`uv run pytest py/tests/viz/test_themes.py -q`
