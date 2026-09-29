# Phase 2 — `LabelShape` unification + `mask` fidelity

## Goal

Unify the example's `LabeledShape` into `LabelShape` (add `mask`/`style`/`act`,
optional `points`/`shape_type`, `description: str | None`), and round-trip the
`mask` field.

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Files

- Edit: `py/pytanga/viz/labelme.py`
- Edit: `py/examples/apps/image_labeling_app.py`
- Edit: `py/tests/viz/test_labelme.py`

## Steps

- [ ] **2.1 — Extend `LabelShape`**
  - Add `mask: str | None = None`, `style: ObjVizStyle | None = None`,
    `act: Any = field(default=None, repr=False, compare=False)`; make `points`/
    `shape_type` optional (default empty); change `description` to `str | None`
    (default `None`, no `""` coercion).
- [ ] **2.2 — Round-trip `mask` + preserve `None` description**
  - `loads` reads `mask` and keeps `description` as `None` when absent; `dumps`
    writes `mask` when present (and omits `None` description, as labelme does).
- [ ] **2.3 — Refactor `ImageLabeler`**
  - Delete `LabeledShape`; keep `list[LabelShape]` with `act`/`style`/`label`
    populated; adapt `as_pair` to a `LabelShape`-based export path.
- [ ] **2.4 — Tests**
  - `mask` round-trips through `loads`/`dumps`; `description` `None` survives;
    `style`/`act` never appear in `dumps` output.

## Validation

```
uv run pytest py/tests/viz/test_labelme.py -q && uv run ruff check . && uv run ty check
```

## Notes

- `style`/`act` are excluded from `to_dict`/`from_dict`/`dumps`/`loads` (labelme
  has no such concept). `mask` is opaque and always round-tripped verbatim.
