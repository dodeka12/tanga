# Geometry `mask_for` hard-coded type masks — Overview

**Created:** 2026-09-18 | **Status:** Done | **Branch:** `feat/expression-matrix`

## Goal

Replace the fragile, instance-derived `mask_for` with **hard-coded blade masks per
entity/operator type per algebra**.  Today `mask_for` builds a generic instance
(`_template`) and takes its non-zero blades, which silently produces *partial*
masks when the template's fixed numbers land on a zero coefficient (e.g. N2
`Sphere(Point(1,2,3), 2.0)` drops `ep` because `r² = |c|² − 1`).  Each supported
type must instead declare its full blade set explicitly.

## Architecture (short)

- **Fixed contract** — every `create_*` module exposes
  `mask_for_<key>(basis) -> BladeMask` for each supported type, hard-coding the
  full blade ids (and attaching the named basis inline, auto display basis by
  default or an explicit `with_basis` for reduced types like `TwistBivector`).
- `pytanga.geometry.mask.mask_for(basis, typ)` dispatches:
  - **class** → `create_*.mask_for_<key>(basis)` (hard-coded full type mask);
  - **instance** → `BladeMask(_create(basis, instance))` (the instance's actual
    non-zero blades — this part stays, since it is inherently instance-specific).
- Remove `_template` and the `basis_for` dispatcher; the named-basis hook is
  folded into `mask_for_<key>` (which returns the mask already carrying its basis).

## Decisions (confirmed)

- **Hard-coded ids, not grades, not instance-derived.**  Each mask is declared as
  an explicit sorted blade-id list (or a `BladeMask` built from those ids).
- **Class vs instance split.**  `mask_for(alg, Type)` returns the full type mask;
  `mask_for(alg, instance)` returns the instance's non-zero blades (unchanged
  semantics, still correct).
- **Named basis is attached inline.**  `mask_for_twist_bivector` returns the
  6-DOF basis mask directly; all other types rely on the auto display basis.
- **One phase per GA basis**: E2, E3, P2, P3, N2, N3, PGA2, PGA3.  Q2/Q3 are
  `pytanga.quadric`, out of scope.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 0 | [00-shared-mask-dispatch.md](./00-shared-mask-dispatch.md) | Rewrite `mask_for` dispatch; drop `_template`/`basis_for`; test helper |
| 1 | [01-e2.md](./01-e2.md) | E2 hard-coded masks |
| 2 | [02-e3.md](./02-e3.md) | E3 hard-coded masks |
| 3 | [03-p2.md](./03-p2.md) | P2 hard-coded masks |
| 4 | [04-p3.md](./04-p3.md) | P3 hard-coded masks |
| 5 | [05-n2.md](./05-n2.md) | N2 hard-coded masks |
| 6 | [06-n3.md](./06-n3.md) | N3 hard-coded masks |
| 7 | [07-pga2.md](./07-pga2.md) | PGA2 hard-coded masks |
| 8 | [08-pga3.md](./08-pga3.md) | PGA3 hard-coded masks |
| 9 | [09-docs-changelog.md](./09-docs-changelog.md) | Docs + changelog + full validation |

## Testing as you go

- `uv run pytest py/tests/geometry/ -q`
- `uv run ruff check py/pytanga/geometry py/tests/geometry`
- `uv run ty check`
- `uv run mkdocs build --strict`

## Non-goals

- No change to `create_*` MV construction results.
- No `BladeMask` / `MVTensor` core changes.
- Q2/Q3 quadric entities.
- Instance-mask semantics stay as-is (non-zero blades of the instance).

---

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.
