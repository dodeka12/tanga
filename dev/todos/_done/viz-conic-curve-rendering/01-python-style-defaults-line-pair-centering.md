# Phase 1 — Backend extent defaults + centered line pairs

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture. If this
> work introduces or changes architecture, update the developer docs.

## Goal

Make the conic curve "sensible size" backend-driven (like `LineStyle.length`),
and make line pairs render symmetrically through their intersection point.

## Files

- Edit: `py/pytanga/viz/_styles/_entity_styles.py` (`HyperbolaStyle`,
  `ParabolaStyle` docstrings)
- Edit: `py/pytanga/viz/_styles/__init__.py` (`_DEFAULT_STYLE_FOR_KIND`)
- Edit: `py/pytanga/viz/serializer.py` (`_serialize_line_pair`,
  `_serialize_parallel_line_pair`)
- Edit: `py/tests/viz/test_conic_renderers.py`, `py/tests/viz/test_serializer.py`

## Steps

- [x] **1.1 — Set `extent` defaults in `_DEFAULT_STYLE_FOR_KIND`.**
  - `"Hyperbola"` and `"Parabola"` entries gain `extent=5.0` (a spatial
    half-size). Update the `HyperbolaStyle`/`ParabolaStyle` docstrings so
    `extent` is documented as a spatial half-size, not a parameter range.
- [x] **1.2 — Center line-pair member lines.**
  - In `_serialize_line_pair` / `_serialize_parallel_line_pair`, resolve the
    member line length from `LinePairStyle`/`ParallelLinePairStyle` (default
    `20.0`, mirroring `LineStyle.length`) and shift each line's `origin` back by
    `length/2` along its unit `direction`, emitting `length` so the frontend
    draws `±length/2`. Reuse/refactor the centering logic already in
    `_serialize_line` if possible.
- [x] **1.3 — Tests.**
  - Assert `_DEFAULT_STYLE_FOR_KIND["Hyperbola"].extent == 5.0` (and parabola).
  - Serialize a `LinePair` whose lines pass through the origin and assert each
    emitted `origin` is centered (`origin == -length/2 · direction`).

## Validation

`uv run pytest py/tests/viz/test_conic_renderers.py py/tests/viz/test_serializer.py py/tests/viz/test_viz_styles.py -q`

## Notes

- The frontend still has a hardcoded `extent` fallback until Phase 3; this phase
  only sets the backend default and wire contract.
