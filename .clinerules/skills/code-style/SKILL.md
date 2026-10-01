---
name: code-style
description: Apply the project coding style guides when writing, editing, or reviewing code. Read docs/dev/guides/py-coding-style-guide.md (Python), docs/dev/guides/js-coding-style-guide.md (JS/TS), docs/dev/guides/cpp-coding-style-guide.md (C++), and docs/dev/architecture/typing-and-annotations.md for the typing policy (annotate everything; avoid Any — use explicit types, unions, or Protocols). Use when authoring, modifying, or reviewing any code.
---

# Code Style

Write and review code against the project's coding style guides.

## Read the guides first

Before touching code, read the guide for the language you are editing:

- Python: `docs/dev/guides/py-coding-style-guide.md`
- JavaScript/TypeScript: `docs/dev/guides/js-coding-style-guide.md`
- C++: `docs/dev/guides/cpp-coding-style-guide.md`
- Typing & annotations (Python): `docs/dev/architecture/typing-and-annotations.md`

## Python rules (must follow)

- PEP 8 — 4-space indent, 100-char lines, `snake_case` / `PascalCase` /
  `UPPER_CASE`.
- Annotate **every** function, method, and dataclass field (`uv run ty check` +
  `uv run ruff check .`).
- **Avoid `Any`** — use an explicit type, a type union (`A | B`), or a
  `Protocol`.  `Any` is only for genuinely dynamic values; `ty` does not flag it
  (`ANN401` disabled), so review must catch it.
- Never access another class's private (`_`) members — use its public API.

## JS/TS and C++

- Follow their guides; the encapsulation rule (no private-member access across
  classes) applies to every language.

## Validation

- Python: `uv run ruff check .`, `uv run ruff format .`, `uv run ty check`.
- Run the linter/formatter for the language you edited.
