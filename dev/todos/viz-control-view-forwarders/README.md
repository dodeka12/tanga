# Viz control view forwarders (remove `__getattr__`) — Overview

**Created:** 2026-10-05 | **Status:** Planned | **Branch:** `fix/small-bugs`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Remove the dynamic `ControlView.__getattr__` shim (which returns `Any`) and
replace it with **explicit, typed forwarders** — `@property` reads (and, where a
view already mutates the model, explicit setters/methods) on the base and each
concrete control view — so the public API is introspectable and type-checked.
Replace the remaining `getattr`/`hasattr` duck-typing in `menu_view` with a
`Protocol`.

## Architecture (short)

- `ControlView[C]` already carries `self.control: C` (a concrete typed
  `Control`), so each concrete view knows its fields' types and can forward them
  explicitly.
- This mirrors the existing repo precedent: `Visualizer.__getattr__` was already
  replaced by explicit thin forwarders (`docs/changelog/2026/09/03_58f34cb0.md`).
- Follows `docs/dev/architecture/typing-and-annotations.md` Rule 2 (avoid
  `Any`; prefer explicit types / unions / `Protocol`).

### Fixed contract (do not change across phases)

1. **No `__getattr__`** remains on `ControlView` (or any control view).
2. Every previously-forwarded **read** has an explicit typed `@property` (or
   method) on the owning view; writes that mutate the model go through explicit
   setters/methods.  Forwarded reads are **read-only** properties (no setter) —
   matching today, where `__getattr__` never forwarded writes.
3. `menu_view._apply_menu_variant` uses a `Protocol` (or `isinstance` union)
   over the variant-carrying controls, not `getattr`/`hasattr`.
4. The public read surface is preserved: `view.min`, `view.value`,
   `view.options`, `view.variant`, `view.on_change` (and per-kind `on_*`),
   `view.undo()` / `view.redo()` / `view.can_undo` / `view.can_redo`,
   `view.enabled` / `view.visible` / `view.selected`, and `view.get_value()`
   keep working.

## Decisions (confirmed)

- Use explicit typed forwarders (not a re-introduced generic `__getattr__`, and
  not `Any`).
- Use a `Protocol` for the structural "has a `variant`" contract in `menu_view`
  (variant-carrying controls are `Slider` / `Button` / `Checkbox` / `Dropdown`).
- Keep the single `cast` at the binding boundary in
  `functions.py::control_to_view` (Rule 2 sanctions it).
- No behavior change — only the typing / forwarding mechanism changes.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-control-view-base.md](./01-control-view-base.md) | Delete `__getattr__`; add base `enabled`/`visible`/`selected` + typed `get_value` |
| 2 | [02-concrete-view-forwarders.md](./02-concrete-view-forwarders.md) | Typed `@property`/setter forwarders for all 13 concrete views |
| 3 | [03-menu-variant-protocol.md](./03-menu-variant-protocol.md) | `Protocol` for variant; re-verify `control_to_view` cast |
| 4 | [04-tests-docs-changelog.md](./04-tests-docs-changelog.md) | Tests + docs + changelog |

## Testing as you go

```bash
uv run ty check                                    # correctness (phases 1-4)
uv run ruff check .                                # lint + ANN coverage (phases 1-4)
uv run pytest py/tests/viz -q                      # Python side (phases 1-4)
uv run mkdocs build --strict                       # docs (phase 4)
```

## Non-goals

- No change to the `Control` dataclass fields or the wire format.
- No new control kinds.
- No behavior change — only the typing / forwarding mechanism changes.
