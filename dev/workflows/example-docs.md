# Workflow: Example Docs

How to write the header comments so a new example under `py/examples/` shows up
in the generated docs gallery (searchable by keyword, with its source code
embedded).

## `.py` examples

Every new `.py` example must start with the license header followed by a module
docstring containing, in order:

1. a one-line description as the first line, in the `<name>.py — …` form;
2. (optional) a longer explanation;
3. a `Run with:` line giving the command to run it;
4. a trailing `Keywords: <comma-separated list>` line.

```python
"""orbit.py — Frame-by-frame animation at ~60 FPS.

Run with:  uv run python py/examples/viz/animation/orbit.py

Keywords: animation, frame streaming, animate, orbit, Point
"""
```

## `.ipynb` examples

For notebooks, put the same information in the **first markdown cell**: an H1
title, an optional description, and a trailing `Keywords:` line.

## Keywords

- Keep each list short (3–8 terms).
- Use task-oriented terms and reuse them across related examples (e.g.
  `animation`, `frame streaming`, `orbit`) so MkDocs search clusters them.
- Prefer comma separation; commas inside parentheses (e.g. `G(3,0)`) are kept
  intact by the generator.

## After adding or editing an example

Regenerate the docs pages and nav so the example appears (and stays in sync):

```bash
uv run python tools/generate-example-docs.py
uv run python tools/generate-example-docs.py --check   # CI/drift gate
```

Then run `uv run mkdocs build --strict` to verify the page renders and is
reachable from the "Examples" navigation.
