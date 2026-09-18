# Geometry `mask_for` named-basis sweep — Overview

**Created:** 2026-09-18 | **Status:** Done | **Branch:** `feat/expression-matrix`

## Goal

Ensure every `mask_for(basis, typ)` result in `pytanga.geometry` carries the
correct **named basis** (`basis_names` / `basis_vectors`), not just raw blade
ids.  Sweep one algebra basis per phase: scan every `BladeMask`-creating path,
and adapt it so `mask_for(typ).basis_names` reports the canonical directions for
that type in that algebra.

## Architecture (short)

- `mask_for` already builds `BladeMask(_create(basis, template))` and attaches a
  named basis via `with_basis(...)` when `basis_for(basis, typ)` returns one
  (`py/pytanga/geometry/mask.py`).
- `BladeMask._attach_display_basis` (Phase 1 of `expression-basis-tensor`)
  already auto-attaches the algebra display basis when it covers the mask, so
  full-grade masks already carry names (e.g. `mask_for(Point)` in N3 →
  `e1, e2, e3, einf, eo` over ids `1, 2, 4, 8, 16`).
- **Fixed contract** — `basis_for(basis, typ) -> list[tuple[str, MV]] | None` is
  extended from the single `TwistBivector` branch into a full per-type dispatcher
  mirroring `create_operator`; per-algebra `basis_for_<type>(basis)` functions
  live in the `create_*` modules.  `None` → keep the auto display basis.

## Decisions (confirmed)

- **Default = auto display basis.**  A type-specific basis is added only where
  the physical DOF differs from the display basis (reduced/partial), e.g.
  `TwistBivector`'s 6 directions over 9 raw blades.
- **One phase per GA basis**: E2, E3, P2, P3, N2, N3, PGA2, PGA3.  Q2/Q3 live in
  `pytanga.quadric` and are out of scope.
- **Each phase**: scan (enumerate supported types + current names), adapt (add
  `basis_for_<type>` hooks where needed), test (pin names).
- No change to `create_*` MV results or to `BladeMask`/`MVTensor` core.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 0 | [00-shared-basis-dispatch.md](./00-shared-basis-dispatch.md) | Extend `basis_for` dispatcher + test helper |
| 1 | [01-e2.md](./01-e2.md) | E2 sweep |
| 2 | [02-e3.md](./02-e3.md) | E3 sweep |
| 3 | [03-p2.md](./03-p2.md) | P2 sweep |
| 4 | [04-p3.md](./04-p3.md) | P3 sweep |
| 5 | [05-n2.md](./05-n2.md) | N2 sweep |
| 6 | [06-n3.md](./06-n3.md) | N3 sweep |
| 7 | [07-pga2.md](./07-pga2.md) | PGA2 sweep |
| 8 | [08-pga3.md](./08-pga3.md) | PGA3 sweep |
| 9 | [09-docs-changelog.md](./09-docs-changelog.md) | Docs + changelog + full validation |

## Testing as you go

- `uv run pytest py/tests/geometry/ -q`
- `uv run ruff check py/pytanga/geometry py/tests/geometry`
- `uv run ty check`
- `uv run mkdocs build --strict`

## Non-goals

- No change to `create_*` MV construction — only the `BladeMask` named basis.
- No `BladeMask` / `MVTensor` core changes (already landed).
- Q2/Q3 quadric entities.
- No visualization or analysis changes.

---

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.
