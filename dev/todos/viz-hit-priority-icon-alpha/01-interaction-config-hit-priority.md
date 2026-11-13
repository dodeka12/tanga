# Phase 1 — `InteractionConfig.hit_priority` and `ActPoint` opt-in

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.
> Reference: `docs/dev/architecture/viz-controls-and-interactions.md`
> (`## Interactive objects`, `### Active object handle controls`).

## Goal

Give picking an explicit, backend-controlled precedence signal: a new
`InteractionConfig.hit_priority` field (always serialized, default `0`) and an
`ActPoint(hit_priority=10)` opt-in, so every control point outranks the body it
sits on.  Frontend consumption is phase 2 — this phase only ships the model and
its tests.

## Files

- Edit: `py/pytanga/viz/_interaction.py`
- Edit: `py/pytanga/viz/_active.py`
- Edit: `py/tests/viz/test_interaction_config.py`
- Edit: `py/tests/viz/test_active.py`
- Edit: `py/tests/viz/test_act_circle.py`

## Steps

- [x] **1.1 — `InteractionConfig.hit_priority` (`_interaction.py`)**
  - Add the field directly after `throttle_ms: int = 50` (line ~179):
    ```python
    hit_priority: int = 0
    ```
  - Class docstring (`Attributes:` block, after `throttle_ms`): document it as
    *"Pick precedence when several interactive entities are hit at the pointer;
    higher wins.  ``0`` = default body precedence; :class:`ActPoint` handles use
    ``10`` so a control point beats the geometry it sits on."*
  - `to_dict()`: add `"hit_priority": self.hit_priority,` to the always-emitted
    block next to `"throttle_ms"` (line ~188-192).  Do **not** guard it with
    `if ... is not None` — the frontend must always receive a number.

- [x] **1.2 — `ActPoint(hit_priority=10)` (`_active.py`)**
  - `ActPoint.__init__` signature (line 778-795): add keyword-only
    `hit_priority: int = 10,` after `handle_style: PointStyle | None = None,`
    (line 786).
  - Store it next to `self._drag_mode = drag_mode` (line 812):
    ```python
    self._hit_priority: int = int(hit_priority)
    ```
  - Class docstring `Args:` (after the `click_bindings` entry, line ~774): add
    *"hit_priority: Pick precedence against other interactive entities (default
    ``10``).  Control points sit on top of the geometry they edit, so the
    default makes them win over the body (bodies default to ``0``).  Pass ``0``
    to make the point pick like a plain body."*
  - `ActPoint.interaction_config` return (line 900-905): add
    `hit_priority=self._hit_priority,` next to `throttle_ms=40,` (line 901).
  - Do **not** touch `ActiveObject`/composite `interaction_config` bodies — they
    must stay at the `InteractionConfig` default `0`.  Composite handles pick
    this up automatically because they are child `ActPoint`s spawned by
    `_spawn_handle`.

- [x] **1.3 — `test_interaction_config.py` coverage**
  - Extend `TestInteractionConfig`:
    - `test_to_dict_hit_priority_default_zero` — `InteractionConfig(enabled=True).to_dict()["hit_priority"] == 0`
      (assert it is present, i.e. `"hit_priority" in d`).
    - `test_to_dict_hit_priority_custom` — `InteractionConfig(enabled=True, hit_priority=7).to_dict()["hit_priority"] == 7`.

- [x] **1.4 — `test_active.py` coverage**
  - New `class TestHitPriority` right after `TestDragModifiers` (line 304):
    - `test_act_point_defaults_to_ten` — `_init_point()` → `ap.interaction_config.hit_priority == 10`.
    - `test_act_point_hit_priority_override` — `_init_point(hit_priority=0)` → `0`.
    - `test_hit_priority_reaches_the_wire` — the config pushed via
      `_FakeSceneHandle.configs` (`handle.configs[-1][1].to_dict()`) carries the
      same value.

- [x] **1.5 — `test_act_circle.py` composite coverage**
  - Add to `TestHandleControls`:
    - `test_body_keeps_default_priority` — `circle, _ = _circle()` →
      `circle.interaction_config.hit_priority == 0`.
    - `test_handles_are_prioritised` — every handle from
      `circle._all_handles()` has `hit_priority == 10`.

## Validation

```bash
uv run pytest py/tests/viz/test_interaction_config.py py/tests/viz/test_active.py py/tests/viz/test_act_circle.py -q
```

## Notes

- `hit_priority` is a plain `int`, not an enum or a float: precedence is a
  coarse ordering, and an `int` keeps the JSON stable and comparable.
- The field is additive and backward compatible; no `InteractionConfig`
  consumer reads it yet (phase 2 does).
- `ActPoint` is also used for bare, non-handle points — they intentionally get
  `10` too (decision recorded in the plan `README.md`).
