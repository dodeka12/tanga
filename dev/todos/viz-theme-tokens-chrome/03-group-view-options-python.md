# Phase 3 — `GroupView` title & header options (Python)

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Give `GroupView` a real title/header model: `title` becomes `str | None` with
no implicit fallback, `show_header=` removes the whole header bar,
`collapsible=` allows a fixed (non-foldable) group, and `title_size=` overrides
the title font size per instance.  All of it is validated up front and
serialized per the fixed contract in the README.

## Files

- Edit: `py/pytanga/viz/views/group_view.py`
- Edit: `py/tests/viz/test_views.py`

## Steps

- [ ] **3.1 — Constructor signature (`views/group_view.py`)**
  - `title: str = ""` → `title: str | None = ""`; document that `None` and
    `""` both render **no** title (there is no implicit `"Controls"` label).
  - Add keyword-only options after `collapsed`:
    ```python
    show_header: bool = True,
    collapsible: bool = True,
    title_size: float | None = None,
    ```
  - Docstring for each:
    - `show_header` — render the header bar at all; `False` also forces
      `collapsible=False` and keeps the panel padding/border.
    - `collapsible` — render the fold toggle and allow collapsing; `False`
      renders a static (never folding) group.
    - `title_size` — title font size in px, overriding
      `--tanga-group-title-font-size` for this instance only.

- [ ] **3.2 — Validation & normalisation**
  - After assigning the fields:
    ```python
    if not show_header:
        self.collapsible = False
    if collapsed and not self.collapsible:
        raise ValueError(
            "GroupView(collapsed=True) requires collapsible=True and "
            "show_header=True"
        )
    if title_size is not None and title_size <= 0:
        raise ValueError("GroupView(title_size=…) must be > 0")
    ```
  - Assign `self.show_header`, `self.collapsible`, `self.title_size` (new
    fields, next to `self.title` at `:73-83`) **before** the validation block,
    so the checks see the final values.
  - Update the `on_toggle` docstring if it mentions folding, so it states the
    callback is never fired for a non-collapsible group (the toggle is not
    rendered at all).

- [ ] **3.3 — Runtime setters**
  - `set_title(title: str | None)` — accept `None`, store it, and keep pushing
    `{"title": self.title}` (a `None` payload clears the rendered title on the
    client; phase 4 handles it).
  - `set_collapsed(collapsed)` — `if not self.collapsible: raise ValueError(…)`
    before mutating; keep the existing push.
  - Add a short `# show_header / collapsible / title_size are construction-time`
    comment next to the fields so nobody adds a setter later.

- [ ] **3.4 — Serialization**
  - `result["title"] = self.title` stays (now possibly `None`).
  - Always emit `result["show_header"] = self.show_header` and
    `result["collapsible"] = self.collapsible` right after `title`.
  - Emit `result["title_size"] = self.title_size` only when not `None`.

- [ ] **3.5 — Tests (`py/tests/viz/test_views.py`)**
  - `test_group_serialize_title_none` — `GroupView(None)` serializes
    `title is None`, `show_header is True`, `collapsible is True`.
  - `test_group_serialize_header_flags` — defaults serialize
    `show_header=True`, `collapsible=True`; `GroupView("x", show_header=False)`
    serializes `show_header=False` **and** `collapsible=False`.
  - `test_group_title_size_serialized_only_when_set` — absent by default,
    `== 15.0` when passed.
  - `test_group_collapsed_validation` — `GroupView("x", collapsed=True,
    collapsible=False)` and `GroupView("x", collapsed=True, show_header=False)`
    each raise `ValueError`.
  - `test_group_title_size_validation` — `title_size=0` raises `ValueError`.
  - `test_group_set_title_none_pushes_null` — stub `_push_state`, assert the
    pushed payload is `{"title": None}` (mirror the existing `set_title` test).
  - `test_group_set_collapsed_requires_collapsible` — raises on a
    non-collapsible group and pushes nothing.
  - Update any existing test that asserted a `title` default of `""` (still
    true) or that constructed a `collapsed=True` group without `collapsible`
    (default is `True`, so those keep working).

## Validation

```bash
uv run pytest py/tests/viz/test_views.py -q
```

## Notes

- `ParamsView._build_group` always passes a real title and leaves the new
  kwargs at their defaults, so nested groups are unaffected.
- `GroupView` subclasses `StackView`; `show_header` / `collapsible` /
  `title_size` are **new keyword-only** params, so no positional call site
  changes.
