# Phase 3 — `GroupView` options & variants (Python)

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Give `GroupView` a real title/header model: `title` becomes `str | None` with
no implicit fallback, `show_header=` removes the whole header bar,
`collapsible=` allows a fixed (non-foldable) group, `title_size=` overrides
the title font size per instance, and `variant=` selects the presentational
`EGroupVariant` (`default` / `small` / `tiny`) that the CSS re-scopes.  The
`GroupView`s that `ParamsView` creates for its fields are `small` at depth 0
and `tiny` deeper, with `GroupUI.variant` as a per-field override.  All of it
is validated up front and serialized per the fixed contract in the README.

## Files

- Edit: `py/pytanga/viz/views/_enums.py`
- Edit: `py/pytanga/viz/views/__init__.py`
- Edit: `py/pytanga/viz/__init__.py`
- Edit: `py/pytanga/viz/views/group_view.py`
- Edit: `py/pytanga/viz/_params_ui.py`
- Edit: `py/pytanga/viz/views/params_view.py`
- Edit: `py/tests/viz/test_views.py`

## Steps

- [x] **3.1 — `EGroupVariant` string enum (`views/_enums.py`)**
  - Add next to `EStackJustify`:
    ```python
    class EGroupVariant(StrEnum):
        DEFAULT = "default"
        SMALL = "small"
        TINY = "tiny"
    ```
  - Export it from `views/__init__.py` (add it to the `E*` enum import and to
    `__all__` in alphabetical order, before `EOrientation`) and from
    `pytanga/viz/__init__.py` (the enum import block around `EStackDirection`
    and `__all__` around line 399).
  - Docstring on the enum: "Presentational size variant of a `GroupView`;
    `SMALL`/`TINY` only re-scope `--tanga-group-*` tokens, they do not change
    layout semantics."

- [x] **3.2 — Constructor signature (`views/group_view.py`)**
  - `title: str = ""` → `title: str | None = ""`; document that `None` and
    `""` both render **no** title (there is no implicit `"Controls"` label).
  - Add keyword-only options after `collapsed`:
    ```python
    show_header: bool = True,
    collapsible: bool = True,
    title_size: float | None = None,
    variant: EGroupVariant | str = EGroupVariant.DEFAULT,
    ```
  - Docstring for each:
    - `show_header` — render the header bar at all; `False` also forces
      `collapsible=False` and keeps the panel padding/border.
    - `collapsible` — render the fold toggle and allow collapsing; `False`
      renders a static (never folding) group.
    - `title_size` — title font size in px, overriding
      `--tanga-group-title-font-size` for this instance only.
    - `variant` — presentational size variant; `SMALL`/`TINY` re-scope the
      `--tanga-group-*` tokens (padding, title font/background, header
      spacing).  A plain string is accepted and validated.
  - Import `EGroupVariant` from `._enums` next to the other enums.

- [x] **3.3 — Validation & normalisation**
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
    try:
        self.variant = EGroupVariant(variant)
    except ValueError as exc:
        raise ValueError(
            f"GroupView(variant=…): unknown variant {variant!r}; "
            f"expected one of {[v.value for v in EGroupVariant]}"
        ) from exc
    ```
  - Assign `self.show_header`, `self.collapsible`, `self.title_size` and
    `self.variant` (new fields, next to `self.title` at `:73-83`) **before**
    the validation block, so the checks see the final values.  The
    `EGroupVariant(...)` normalisation accepts both the enum and its string
    value (standard `StrEnum` behaviour).
  - Update the `on_toggle` docstring if it mentions folding, so it states the
    callback is never fired for a non-collapsible group (the toggle is not
    rendered at all).

- [x] **3.4 — Runtime setters**
  - `set_title(title: str | None)` — accept `None`, store it, and keep pushing
    `{"title": self.title}` (a `None` payload clears the rendered title on the
    client; phase 4 handles it).
  - `set_collapsed(collapsed)` — `if not self.collapsible: raise ValueError(…)`
    before mutating; keep the existing push.
  - Add a short
    `# show_header / collapsible / title_size / variant are construction-time`
    comment next to the fields so nobody adds a setter later.

- [x] **3.5 — Serialization**
  - `result["title"] = self.title` stays (now possibly `None`).
  - Always emit `result["show_header"] = self.show_header` and
    `result["collapsible"] = self.collapsible` right after `title`.
  - Emit `result["title_size"] = self.title_size` only when not `None`.
  - Emit `result["variant"] = self.variant.value` only when
    `self.variant is not EGroupVariant.DEFAULT`, so the wire stays unchanged
    for every existing group.

- [x] **3.6 — `GroupUI.variant` (`_params_ui.py`)**
  - Add to `GroupUI` next to `collapsed`:
    ```python
    variant: EGroupVariant | str | None = None
    ```
    with a `if TYPE_CHECKING: from .views._enums import EGroupVariant` import
    (the runtime import would run during `views/__init__.py`'s own import —
    keep it type-only; add `TYPE_CHECKING` to the existing `typing` import).
  - Docstring: "Styling variant of the created sub-panel; `None` uses the
    owning `ParamsView`'s depth default (`SMALL` at depth 0, `TINY` deeper)."
  - `EGroupVariant` is a `StrEnum`, so `GroupUI(variant=EGroupVariant.SMALL)`
    and `GroupUI(variant="small")` are equivalent.

- [x] **3.7 — `ParamsView` depth defaults (`views/params_view.py`)**
  - Add a private keyword-only `_group_depth: int = 0` after `key_prefix` (do
    **not** let it fall into `**view_kwargs`; it is not a `View` option).
    Document it as "nesting depth of the `ParamsView`s this view creates; the
    top-level view is 0".
  - Store `self._group_depth = int(_group_depth)`.
  - In `_build_group` (`:230`), before building the nested view:
    ```python
    variant = ui.variant or (
        EGroupVariant.SMALL if self._group_depth == 0 else EGroupVariant.TINY
    )
    ```
  - Pass `_group_depth=self._group_depth + 1` to the nested `ParamsView` and
    `variant=variant` to the returned `GroupView` (next to `collapsed=` and
    `tooltip=`).
  - Import `EGroupVariant` from `._enums` at the top of `params_view.py`.
  - This is the only framework place that creates a sub-group `GroupView`, so
    no other call site changes.

- [x] **3.8 — Tests (`py/tests/viz/test_views.py`)**
  - Import `EGroupVariant` (from `pytanga.viz`) and `GroupUI` in the test
    module alongside the existing imports.
  - `test_group_serialize_title_none` — `GroupView(None)` serializes
    `title is None`, `show_header is True`, `collapsible is True`.
  - `test_group_serialize_header_flags` — defaults serialize
    `show_header=True`, `collapsible=True`; `GroupView("x", show_header=False)`
    serializes `show_header=False` **and** `collapsible=False`.
  - `test_group_title_size_serialized_only_when_set` — absent by default,
    `== 15.0` when passed.
  - `test_group_variant_serialized_only_when_non_default` — no `variant` key
    by default; `GroupView("x", variant=EGroupVariant.SMALL)` serializes
    `"variant": "small"`; `GroupView("x", variant="tiny")` normalises and
    serializes `"variant": "tiny"`.
  - `test_group_variant_validation` — `GroupView("x", variant="huge")` raises
    `ValueError` mentioning `small`/`tiny`.
  - `test_group_collapsed_validation` — `GroupView("x", collapsed=True,
    collapsible=False)` and `GroupView("x", collapsed=True, show_header=False)`
    each raise `ValueError`.
  - `test_group_title_size_validation` — `title_size=0` raises `ValueError`.
  - `test_group_set_title_none_pushes_null` — stub `_push_state`, assert the
    pushed payload is `{"title": None}` (mirror the existing `set_title` test).
  - `test_group_set_collapsed_requires_collapsible` — raises on a
    non-collapsible group and pushes nothing.
  - `test_params_group_variant_defaults_by_depth` — a `ParamsView` over a
    dataclass with a nested dataclass field that itself has a nested dataclass
    field serializes the depth-0 group as `"variant": "small"` and the
    depth-1 group as `"variant": "tiny"` (the `tiny` group is nested inside the
    `small` group's serialized `children`).
  - `test_params_group_variant_override` — a top-level dict source with
    `styles={"shape": GroupUI(variant=EGroupVariant.DEFAULT)}` serializes the
    group **without** a `variant` key, and
    `GroupUI(variant="tiny")` serializes `"variant": "tiny"`, overriding the
    depth-0 `small` default.
  - Update any existing test that asserted a `title` default of `""` (still
    true) or that constructed a `collapsed=True` group without `collapsible`
    (default is `True`, so those keep working).

## Validation

```bash
uv run pytest py/tests/viz/test_views.py -q
```

## Notes

- `ParamsView._build_group` always passes a real title; it now also passes the
  depth-derived `variant`, so a manual `GroupView` (default variant) is
  unaffected.
- `GroupView` subclasses `StackView`; `show_header` / `collapsible` /
  `title_size` / `variant` are **new keyword-only** params, so no positional
  call site changes.
- `variant` is presentational only: it never touches `minSizePx` /
  `preferredPx` / `collapsed` semantics.  A layout re-push is the only way to
  change it after construction.
- `GroupUI` stays importable without importing `views` at runtime (the
  `EGroupVariant` import is `TYPE_CHECKING`-only) — `views/__init__.py` itself
  imports `RowSpec` from `_params_ui`.
- `ParamsView._group_depth` is private; do not expose it as a public option in
  this plan.  It counts only the `ParamsView`s that `_build_group` creates, so
  a manually nested `ParamsView` starts again at depth 0 (its own field groups
  are `small`).  If a caller needs a specific style, use `GroupUI(variant=…)`
  for fields or a manual `GroupView(variant=…)` around the `ParamsView`.
