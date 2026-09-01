For changelog creation/structure/naming conventions, follow dev/workflows/changelog.md.
For opening pull requests, follow dev/workflows/pull-request.md.
When adding or editing an example under `py/examples/`, follow dev/workflows/example-docs.md (description + `Keywords:` header).
Always run Python scripts/tools with `uv run python ...` (not a bare `python ...`) so the project virtual environment and its dependencies are available.
When adding or changing a control, view, or interactive element in `py/pytanga/viz/`, follow the unified controls/interactions architecture in `docs/dev/architecture/viz-controls-and-interactions.md` (one `(id, event)` registry, `ControlView` wraps a `Control`, events sent via `sendEvent`).
