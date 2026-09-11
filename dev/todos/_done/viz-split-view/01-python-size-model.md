# Phase 1 — Python `Size` value type

## Goal

A pure, dependency-free `Size` value type understood by both the Python `View`
model and the frontend. It parses/emits the canonical `{value, unit}` JSON
shape and resolves to pixels given an available extent.

## Steps

- [x] **1.1 — Add `py/pytanga/viz/_size.py`**
  - `Unit` literal type: `"px" | "%" | "fr" | "auto"`.
  - `Size(value: float, unit: Unit)` with `px()/percent()/fr()/auto()` factories.
  - `from_dict(d) -> Size` / `to_dict() -> dict` for the canonical JSON shape
    (and handle `None` ⇄ `auto` for min/max).
  - `resolve(available: float, natural: float | None) -> float | None`:
    `px` → value; `%` → value/100*available; `fr` → natural; `auto` → natural.
  - `__eq__`/`__repr__`/`clone()`.
  - Type alias `SizeSpec = Size | None`.

- [x] **1.2 — Unit tests `py/tests/viz/test_size.py`**
  - `to_dict`/`from_dict` round-trip for all four units and `None`.
  - `resolve` for px/%/fr/auto with a known `available`.
  - Equality and immutability.

- [x] **1.3 — Validate**
  - `uv run pytest py/tests/viz/test_size.py -q` (green).

## Validation

`uv run pytest py/tests/viz/test_size.py -q`

## Notes

- No `pytanga.geometry` or viz imports — keep `_size.py` importable standalone
  so later phases (and the frontend's JS `Size`) stay in lockstep with one spec.
