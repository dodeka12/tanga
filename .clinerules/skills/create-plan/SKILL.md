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

## Plan forms

1. **Single plan file** — `dev/todos/<slug>.md` for small, flat changes: a
   general description plus a flat `- [ ]` step list.
2. **Plan folder** — `dev/todos/<slug>/` for multi-phase work: a `README.md`
   overview plus numbered phase files (`01-*.md`, `02-*.md`, …), each with a
   `## Steps` checklist and a `## Validation` command.

## Procedure

1. Understand the task and confirm scope; resolve any ambiguous decisions with
   the user first.
2. Choose the plan form (file vs folder) based on the change's size and phases.
3. For a folder: write the `README.md` overview (goal, design, fixed contract,
   phases table, testing), then one numbered phase file per phase in dependency
   order.
4. Give every phase a `## Validation` command; make the final phase docs +
   changelog (per `dev/workflows/changelog.md` / `dev/workflows/pull-request.md`).

## Hard rule — never guess

If the task, its scope, or a design decision is ambiguous, stop and ask the
user a specific question. Do not invent details or write a plan against
assumptions.

## Repo conventions

- Plans live under `dev/todos/`; multi-phase plans are folders, single-shot
  plans are files.
- The plan is implemented later by `dev/workflows/implement-plan.md`.
- Run Python with `uv run python ...` / `uv run pytest ...` (never bare
  `python`).
