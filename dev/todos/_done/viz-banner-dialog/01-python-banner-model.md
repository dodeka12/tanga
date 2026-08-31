# Phase 1 — Python `Banner` model + serialization

## Goal

Add the backend data model and wire serialization for banners, mirroring the
existing `Control` / `ControlGroup` + `serialize_controls` approach.

## Steps

- [x] **1.1 — `serialize_control_defs` helper (`_controls.py`)**
  - Extract the per-control dict building from `serialize_controls` into
    `serialize_control_defs(controls: list[Control]) -> list[dict]` (reusing
    `_serialize_one_control`), so banners can serialize the same control shapes.
  - Keep `serialize_controls` behaviour unchanged (delegate to the helper for
    the orphan / control lists).

- [x] **1.2 — `Banner` dataclass (`py/pytanga/viz/_banner.py`, new)**
  - Fields: `id: str`, `text: str`, `title: str = ""`,
    `align_x: float = 0.5`, `align_y: float = 0.5`,
    `auto_hide: bool = True`, `dismissable: bool = True`,
    `controls: list[Control] = field(default_factory=list)`,
    `on_close: Handler | None = None`.
  - Validate `align_x` / `align_y` ∈ `[0, 1]`.

- [x] **1.3 — Serializers (`_banner.py`)**
  - `serialize_banner(banner, scene: str | None = None) -> dict` producing the
    `banner_define` message per the README wire contract (`scene=None` →
    `null`; else the scene name string).
  - `serialize_banner_remove(banner_id, scene=None) -> dict`.
  - `serialize_banner_clear(scene=None) -> dict`.

- [x] **1.4 — Export**
  - Export `Banner` from `py/pytanga/viz/__init__.py` (and `__all__`).

- [x] **1.5 — Tests (`py/tests/viz/test_banner.py`, new)**
  - `serialize_banner` shape: global (`scene=None` → `null`) and scoped
    (`scene="detail"`, `scene=""`).
  - Controls serialized with kind-specific fields (slider/dropdown/button).
  - `align_x` / `align_y` out of `[0,1]` raise `ValueError`.
  - `serialize_banner_remove` / `serialize_banner_clear` shapes.

## Validation

`uv run pytest py/tests/viz/test_banner.py -q`
