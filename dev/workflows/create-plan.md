# Workflow: Create a Plan

How to author a tracked implementation plan under `dev/todos/`. Plans come in
two forms; this workflow describes the multi-phase **plan folder** form in
detail, and how to choose between the two. The plan is later executed step by
step by `dev/workflows/implement-plan.md`.

## Choosing the form

1. **Single plan file** — `dev/todos/<slug>.md` — for small, flat changes: a
   general description plus a flat `- [ ]` step list (e.g.
   `dev/todos/viz-export-camera.md`). Use this when the work has no natural
   internal phases.
2. **Plan folder** — `dev/todos/<slug>/` — for multi-phase work: a `README.md`
   overview plus numbered phase files. Use this when the change:
   - has several independently shippable phases (e.g. Python model → server →
     frontend → docs);
   - needs a stable up-front design or wire contract that later phases implement
     against;
   - touches several subsystems (Python, JS, docs, tests) in a defined order.

## Folder layout

```
dev/todos/<slug>/
├── README.md
├── 01-<phase-slug>.md
├── 02-<phase-slug>.md
└── ...
```

- `<slug>` is `<scope>-<topic>`, e.g. `viz-split-view`, `docs-example-gallery`,
  `viz-control-value-api`.
- Phase files are **zero-padded two-digit** numbers in implementation order:
  `01-….md`, `02-….md`, ….
- A phase split into sibling pieces uses a **letter suffix**:
  `06a-….md`, `06b-….md`, `06c-….md` (still read in numeric-then-letter order).
- A phase that grows too large becomes a **nested folder**
  (`13-<slug>/README.md` + `part-a-….md`, `part-b-….md`, …) with a `## Parts`
  table instead of `## Phases`. See
  `dev/todos/viz-sdf-viewer/13-algebra-result-mask-analytic-gradient/` for an
  example.

## `README.md` — the overview

The `README.md` is the single place that explains *what* and *why*; the phase
files explain *how*. Use this shape:

```markdown
# <Name> — Overview

**Created:** YYYY-MM-DD | **Status:** Planned | **Branch:** `<branch-name>`

## Goal

<What the plan delivers, in plain language.>

## Architecture (short)

<The design in a few bullets: key files, data flow, the fixed up-front
contract.>

## Decisions (confirmed)

- <Decisions fixed before any implementation.>

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-<slug>.md](./01-<slug>.md) | <one-line summary> |
| 2 | [02-<slug>.md](./02-<slug>.md) | <one-line summary> |

## Testing as you go

- <Per-subsystem validation commands, run each phase.>

## Non-goals

- <Explicitly out-of-scope items.>
```

Guidance:

- **`Status:`** starts `Planned`, moves to `In progress` as phases complete, and
  `Done` when the plan is finished (see `dev/workflows/implement-plan.md`).
  Keep it current.
- **`Goal`** states the outcome, not the steps. If there are two competing
  approaches, pick one and record it under `Decisions (confirmed)`.
- **`Architecture (short)` / `Background`** — enough design that each phase file
  can stay focused. For wire/API changes, include the canonical contract here
  (the exact JSON/API shape), marked as fixed up front.
- **`Phases` table** — one row per phase file, in order. The table is the index
  an implementer reads first.
- **`Testing as you go`** — list the validation commands per subsystem (Python
  `uv run pytest`, JS `node --test`, docs `uv run mkdocs build --strict`).
- **`Non-goals`** — list what is deliberately out of scope so the plan has a
  hard edge.

## Phase files

Each phase is one file named `NN-<slug>.md` (or `NNa-<slug>.md`). Use this
shape:

```markdown
# Phase N — <Title>

## Goal

<What this phase delivers.>

## Files

- New: `<path>`
- Edit: `<path>`

## Steps

- [ ] **N.1 — <Step title>**
  - <Concrete, checkable detail.>
- [ ] **N.2 — <Step title>**
  - <Concrete, checkable detail.>

## Validation

`<command>`

## Notes

- <Anything the implementer needs to know.>
```

Guidance:

- **Number steps `N.M`** to match the phase number (`1.1`, `1.2`, …; `6a.1`,
  …). The commit message for a step is `type(scope): N.M — <summary>` (see
  `dev/workflows/implement-plan.md`).
- **One step = one committable, checkable unit.** Each `- [ ]` step must be
  small enough to implement, validate, and commit alone. Nested `- [ ]`
  checklists are for the step's concrete details, not separate steps.
- **`## Validation` is mandatory** — a single, runnable command (pytest / lint /
  build / smoke) that gates the phase. Every phase ends with a runnable
  validation; there is no "test phase at the end".
- **`## Files`** (optional) — list the new/edited files up front so the
  implementer knows the blast radius.
- **`## Notes`** (optional) — caveats, references, or decisions specific to the
  phase.

## Authoring principles

- **Fix the contract first.** The wire format, base API, or data model is
  decided and written in the `README.md` up front; later phases implement
  *against* it and never change it (the no-refactor rule). This keeps phases
  independent and orderable.
- **Order phases by dependency.** Models before serializers before frontend;
  a vertical slice before the full build-out; docs + changelog last.
- **Make the final phase docs + changelog**, referencing
  `dev/workflows/changelog.md` (branch changelog) and
  `dev/workflows/pull-request.md` (hash rename + PR).
- **Name the files after what they do**, not their number:
  `01-python-size-model.md`, `04-server-multi-scene.md`,
  `11-docs-changelog.md`.
- **Keep steps actionable.** Avoid "consider", "maybe", "TBD". If a step's
  scope or acceptance criteria is unclear, resolve it with the user before
  writing it (never guess — see `dev/workflows/implement-plan.md`).

## Checklist

- [ ] Chose the right form (single file vs folder) for the change's size.
- [ ] Wrote `README.md` with `Goal`, design, `Phases` table, and `Testing as
      you go`.
- [ ] Fixed the contract/decisions up front in the `README.md`.
- [ ] One numbered phase file per phase, in dependency order.
- [ ] Each phase has `## Steps` (`- [ ]`, numbered `N.M`) and a `## Validation`
      command.
- [ ] Final phase is docs + changelog (per `changelog.md` / `pull-request.md`).
- [ ] `Status:` line set to `Planned`.
