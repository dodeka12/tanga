---
name: implement-plan
description: Implement a tracked plan (a single plan file or a plan folder under dev/todos/) phase by phase and step by step — validate each step, mark it complete in the plan, and commit. Use when the user asks to implement, execute, or work through a plan, or references a file or folder under dev/todos/.
---

# Implement Plan

Implement a tracked implementation plan **phase by phase and step by step**,
validating and committing each step before moving on.

## Read the full workflow first

Read and follow `dev/workflows/implement-plan.md` — it is the authoritative,
step-by-step procedure (plan forms, process, marking, commit style, and the
ambiguity rule).

## Plan forms

1. **Single plan file** — a general description plus a flat `- [ ]` step list
   (e.g. `dev/todos/viz-export-camera.md`).
2. **Plan folder** — a `README.md` overview plus numbered phase files
   (`01-*.md`, `02-*.md`, …), each with `## Steps` checklists and a
   `## Validation` section (e.g. `dev/todos/viz-split-view/`).

## Procedure

1. Read the plan (file, or folder `README.md` + phases in numeric order).
2. Implement **one step** only.
3. Run that step's validation command; continue only when it passes.
4. Mark the step `- [x]` in the plan and commit (code + plan) with a
   conventional message, e.g. `feat(viz): 2.3 — Button icon/icon_only`.
5. Repeat for the next step, then the next phase.

## Hard rule — never guess

If the plan or a step is ambiguous, stop and ask the user a specific question.
Do not assume or invent details, and do not implement.

## Repo conventions

- Run Python with `uv run python ...` / `uv run pytest ...` (never bare
  `python`).
- Follow `dev/workflows/changelog.md` and `dev/workflows/pull-request.md` when
  relevant.
