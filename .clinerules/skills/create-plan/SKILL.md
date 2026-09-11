---
name: create-plan
description: Author a tracked implementation plan under dev/todos/ — a single plan file or a multi-phase plan folder (README.md overview + numbered phase files with ## Steps checklists and a ## Validation section each). Use when the user asks to plan, design, break down, or scope a task, feature, fix, or change into a tracked plan before implementing.
---

# Create Plan

Author a tracked implementation plan under `dev/todos/` — either a single plan
file or a multi-phase plan folder — that `implement-plan` can later execute
phase by phase and step by step.

## Read the full workflow first

Read and follow `dev/workflows/create-plan.md` — it is the authoritative guide
to the plan-folder layout, the `README.md`/phase templates, and the authoring
principles (fix the contract up front, validation per phase, docs + changelog
last).

## Check the developer documentation

Always read the developer documentation for the subsystem(s) the change touches
before writing the plan files — `docs/dev/` in general and, for anything that
touches the architecture, `docs/dev/architecture/` (e.g. `viz-architecture.md`,
`viz-controls-and-interactions.md`).  The plan must make new code align with the
documented architecture, not silently diverge from it.

- Note the relevant developer doc(s) in the plan (see the required notes below).
- If the change would require **extending or modifying** the architecture — a new
  seam, protocol, host/control pattern, or a change to a documented contract in
  `docs/dev/architecture/` — **stop and ask the user to confirm before writing
  the whole plan.**  Do not assume the extension is acceptable.

## Required notes in every plan file

Every plan file (a single plan file, and the `README.md` plus each numbered
phase file of a multi-phase plan) must contain this note so the implementer
re-checks the developer docs:

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Plan forms

1. **Single plan file** — `dev/todos/<slug>.md` for small, flat changes: a
   general description plus a flat `- [ ]` step list.
2. **Plan folder** — `dev/todos/<slug>/` for multi-phase work: a `README.md`
   overview plus numbered phase files (`01-*.md`, `02-*.md`, …), each with a
   `## Steps` checklist and a `## Validation` command.

## Procedure

1. Understand the task and confirm scope; resolve any ambiguous decisions with
   the user first.
2. Check the developer documentation (`docs/dev/`, especially
   `docs/dev/architecture/`) for the affected subsystem(s); note the relevant
   doc(s) in the plan.  If the architecture needs to be extended or modified,
   stop and confirm with the user before writing the whole plan.
3. Choose the plan form (file vs folder) based on the change's size and phases.
4. Add the required architecture note (see above) to the plan file, and — for a
   folder — to the `README.md` and every numbered phase file.
5. For a folder: write the `README.md` overview (goal, design, fixed contract,
   phases table, testing), then one numbered phase file per phase in dependency
   order.
6. Give every phase a `## Validation` command; make the final phase docs +
   changelog (per `dev/workflows/changelog.md` / `dev/workflows/pull-request.md`),
   and include a step to update the developer docs if the work introduced or
   modified architecture.

## Hard rule — never guess

If the task, its scope, or a design decision is ambiguous, stop and ask the
user a specific question. Do not invent details or write a plan against
assumptions.

Likewise, if the plan would require extending or modifying the documented
architecture (`docs/dev/architecture/`), stop and ask the user to confirm that
extension before writing the whole plan.

## Repo conventions

- Plans live under `dev/todos/`; multi-phase plans are folders, single-shot
  plans are files.
- The plan is implemented later by `dev/workflows/implement-plan.md`.
- Run Python with `uv run python ...` / `uv run pytest ...` (never bare
  `python`).
