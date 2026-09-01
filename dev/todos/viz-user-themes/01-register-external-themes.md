# Phase 1 — Register external themes

## Goal

Teach the theme registry to hold **external themes** (a local folder with
`tokens.css` + optional `overrides/*.css`) alongside the bundled ones, and
expose `register_theme(name, path)`. Resolution must now carry **two** paths per
file — the URL-relative *served* path and the absolute *source* path — so both
the live server and the export bundler can resolve an external theme.

## Files

- Edit: `py/pytanga/viz/_themes.py`
- Edit: `py/pytanga/viz/__init__.py` (export `register_theme`)
- Edit: `py/tests/viz/test_themes.py`

## Steps

- [ ] **1.1 — `_ResolvedCss` record**
  - Add an internal dataclass `_ResolvedCss(served_rel: str, source: Path)`.
  - Refactor `ThemeRegistry._resolve()` to return `list[_ResolvedCss]` instead
    of `list[Path]`, keeping the current bundled resolution order
    (`base → tokens → theme tokens → components → overrides`) intact and
    byte-identical for bundled themes.

- [ ] **1.2 — External theme state**
  - Add `self._external: dict[str, _ExternalTheme]` (id → `{label, dir,
    served_prefix, tokens_rel, overrides}`).
  - Add `register(theme_id, theme_dir, label=None)`:
    - reject empty ids and collisions with bundled or already-registered ids;
    - require `theme_dir/tokens.css`;
    - auto-discover flat `theme_dir/overrides/*.css` (sorted by name);
    - default the label to the id.
  - Keep `list_themes()` = bundled + external; keep `default_theme()` = first
    **bundled** theme (`"dark"`).

- [ ] **1.3 — Served vs source resolution**
  - For an external theme, resolve:
    - `base`, default `tokens`, and `components` from the bundled dir
      (`served_rel` = path relative to `themes/`, `source` = under `_themes_dir`);
    - the theme tokens from `theme_dir/tokens.css`
      (`served_rel` = `user/<id>/tokens.css`);
    - each override from `theme_dir/overrides/*.css`
      (`served_rel` = `user/<id>/overrides/<name>.css`).
  - `theme_css_files(id)` → `[r.served_rel for r in _resolve(id)]`.
  - `theme_css_paths(id)` → `[r.source for r in _resolve(id)]`.

- [ ] **1.4 — `external_theme_dirs()`**
  - Add `external_theme_dirs() -> dict[str, Path]` returning
    `{"user/<id>": theme_dir}` for every registered theme (used by the server in
    Phase 2).

- [ ] **1.5 — Module API + exports**
  - Add module-level `register_theme(theme_id, theme_dir, *, label=None)` that
    delegates to the singleton registry.
  - Export `register_theme` (and `external_theme_dirs`) from
    `py/pytanga/viz/__init__.py` (`__all__`).

- [ ] **1.6 — Tests (`test_themes.py`)**
  - Register a temp-dir theme (`tmp_path`) with `tokens.css` + two overrides;
    assert `theme_css_files()` returns the expected served order
    (`base.css`, `tokens.css`, `user/<id>/tokens.css`, `*_COMPONENTS`,
    `user/<id>/overrides/*.css`).
  - Assert `theme_css_paths()` returns absolute paths into the temp dir.
  - Assert `list_themes()` includes the external id and `default_theme()` is
    still `"dark"`.
  - Duplicate id raises; missing `tokens.css` raises.
  - `generate_theme_css(theme_id)` (export path) inlines the external files.

## Validation

`uv run pytest py/tests/viz/test_themes.py -q`
