# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Validate the example notebooks shipped under ``py/examples/ga/jupyter/``.

Jupyter executes each code cell as an independent compilation unit, so these
tests parse cells individually (rather than concatenating them) and check that
every code cell is syntactically valid Python.
"""

from __future__ import annotations

import json
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_NOTEBOOKS_DIR = _REPO_ROOT / "py" / "examples" / "ga" / "jupyter"

_EXPECTED_NOTEBOOKS = {"interactive.ipynb", "animation.ipynb", "export.ipynb"}


def _notebook_paths() -> list[Path]:
    return sorted(_NOTEBOOKS_DIR.glob("*.ipynb"))


def _cell_source(cell: dict) -> str:
    source = cell["source"]
    return "".join(source) if isinstance(source, list) else source


def test_notebook_directory_is_present():
    assert _NOTEBOOKS_DIR.is_dir(), f"missing {_NOTEBOOKS_DIR}"


def test_expected_notebooks_exist():
    names = {p.name for p in _notebook_paths()}
    assert _EXPECTED_NOTEBOOKS <= names, (
        f"missing notebooks: {sorted(_EXPECTED_NOTEBOOKS - names)}"
    )


def test_notebook_code_cells_compile():
    for path in _notebook_paths():
        notebook = json.loads(path.read_text(encoding="utf-8"))
        assert notebook.get("nbformat") == 4, f"{path.name} is not nbformat 4"
        cells = notebook.get("cells", [])
        assert cells, f"{path.name} has no cells"
        for idx, cell in enumerate(cells):
            if cell.get("cell_type") != "code":
                continue
            source = _cell_source(cell)
            # Compile each cell separately, exactly like Jupyter does.
            compile(source, f"{path.name}#cell{idx}", "exec")
