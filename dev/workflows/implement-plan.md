# Workflow: Implement a Plan

How to implement a tracked implementation plan step by step. Plans live under
`dev/todos/` and come in two forms (see below).

## Plan forms

1. **Single plan file** — e.g. `dev/todos/viz-export-camera.md`: a general
   description plus a flat list of steps, each prefixed `- [ ]`.
2. **Plan folder** — e.g. `dev/todos/viz-split-view/`: a `README.md` overview
   plus one numbered phase file per implementation phase
   (`01-….md`, `02-….md`, …). Each phase file has a `## Steps` section with
   `- [ ]` checkboxes and a `## Validation` section.

## Core rules

- Implement **phase by phase** and, within a phase, **step by step**. Never
  work on several steps at once.
- After a step is implemented **and** its validation passes:
  1. mark the step complete in the plan (`- [ ]` → `- [x]`);
  2. create a commit for that step.
- Then continue with the next step, and with the next phase after the phase's
  last step.
- **Ambiguity is a hard stop.** If a step or the plan is ambiguous, do **not**
  guess — stop and ask the user a specific question.

## Process

### 1. Read and scope

- Read the plan file, or (for a folder) the `README.md` and every phase file in
  numeric order.
- Build the ordered list of steps.
- Note each step's/phase's `## Validation` command — that is the gate you must
  pass before committing.

### 2. Implement one step

- Implement only what that single step describes; do not drift into later
  steps or refactor unrelated code.
- Follow repo conventions (`.clinerules`, `dev/workflows/*`).

### 3. Validate the step

- Run the step's validation command (pytest / lint / import smoke / manual
  smoke).
- Only proceed when it passes. If it fails, fix the step (still within scope)
  and re-run.

### 4. Mark complete + commit

- Update the plan file: flip the step's `- [ ]` to `- [x]`.
  - Folder plans: optionally bump the `README.md` `**Status:**` line
    (`Planned` → `In progress` → `Done`) as phases complete.
- Commit the step's code **and** the plan-file update together, with a
  conventional commit message:

  - folder plan: `type(scope): <phase>.<step> — <summary>`
  - single file: `type(scope): <step> — <summary>`

  Example: `feat(viz): 2.3 — Button icon/icon_only`.

### 5. Repeat

- Continue with the next step in the same phase, then the next phase.

## Marking conventions

- `- [ ]` — not started / in progress.
- `- [x]` — implemented and validated (committed).
- Folder-plan `README.md` `**Status:**` — keep it current
  (`Planned` / `In progress` / `Done`).

## Ambiguity rule (hard stop)

If the plan, a step, its acceptance criteria, or its validation command is
ambiguous or lacks enough detail to implement confidently:

1. Stop immediately.
2. Ask the user one specific, answerable question.
3. Do not implement, and do not fill in missing details yourself.

## Checklist

- [ ] Read the plan (file, or folder README + phases in order).
- [ ] Implement exactly one step.
- [ ] Run the step's validation; it passes.
- [ ] Mark the step `- [x]` in the plan.
- [ ] Commit code + plan update with a conventional message.
- [ ] Repeat for the next step / phase.
- [ ] Ambiguity → stop and ask, never guess.
