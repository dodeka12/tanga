# Phase 5 — Output fidelity

## Goal

`dumps`/`save` are lossless and produce labelme-shaped output: no coordinate
rounding by default, a fixed key order, and the `mask` field preserved.

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Files

- Edit: `py/pytanga/viz/labelme.py`
- Edit: `py/tests/viz/test_labelme.py`
- New: `py/tests/viz/data/` (small, license-clear sample labelme file)

## Steps

- [ ] **5.1 — `coordinate_precision` opt-in**
  - `LabelMeStore(coordinate_precision: int | None = None)`; `None` = full
    precision (default), `int` = round to that many decimals.
- [ ] **5.2 — Key order + indent**
  - `dumps` uses `indent=4` and the labelme writer's key order (`version, flags,
    shapes, imagePath, imageData, imageHeight, imageWidth`); drop `sort_keys=True`.
- [ ] **5.3 — `mask` round-trip**
  - Ensure `mask` is written when present and read back (already wired in phase 2;
    verify end-to-end here).
- [ ] **5.4 — Round-trip test**
  - `loads(dumps(doc)) == doc` for a synthetic doc plus a bundled real-file fixture
    (add a small, license-clear sample under `py/tests/viz/data/`).

## Validation

```
uv run pytest py/tests/viz/test_labelme.py -q && uv run ruff check . && uv run ty check
```

## Notes

- Breaking for anyone golden-testing old output; document under "Breaking".
