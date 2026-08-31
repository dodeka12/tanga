# Phase 1 — Python icon model

## Goal

A tiny, dependency-free icon model: `family:name` ids, `StrEnum` collections for
autocompletion, and a grammar helper. No rendering knowledge here — the
family→font mapping lives in the frontend (`createIconElement`).

## Steps

- [x] **1.1 — Add `py/pytanga/viz/_icons.py`**
  - `class EIconMaterial(StrEnum)` — curated starter set of Google Material
    Icons ligature names, values `material:<name>` (e.g.
    `SETTINGS = "material:settings"`, `PLAY_ARROW = "material:play_arrow"`,
    `REFRESH = "material:refresh"`, `ADD = "material:add"`,
    `DELETE = "material:delete"`, `CLOSE = "material:close"`, …).
  - `class EIconUC(StrEnum)` — Unicode symbols, values `uc:<glyph>` (e.g.
    `PLAY = "uc:▶"`, `PAUSE = "uc:⏸"`, `STOP = "uc:⏹"`, `GEAR = "uc:⚙"`,
    `CLOSE = "uc:✕"`, `CHECK = "uc:✓"`, …).
  - Type alias `Icon = EIconMaterial | EIconUC | str`.
  - `icon_family(icon_id: str) -> str` — prefix before the first `:`, default
    `"material"` when there is no `:`.
  - `icon_name(icon_id: str) -> str` — part after the first `:` (whole string
    when no `:`).

- [x] **1.2 — Unit tests `py/tests/viz/test_icons.py`**
  - Enum values carry the full `family:name` id.
  - `icon_family`/`icon_name` for `material:settings`, `uc:▶`, and a bare
    `settings`.
  - `Icon` accepts an enum member and a raw string.

- [x] **1.3 — Validate**
  - `uv run pytest py/tests/viz/test_icons.py -q` (green).

## Validation

`uv run pytest py/tests/viz/test_icons.py -q`

## Notes

- Mirror `_colors.py` (also a `StrEnum` module) — importable standalone, no
  viz/server imports.
- The curated set is a starter; members can be added without code changes
  elsewhere.
