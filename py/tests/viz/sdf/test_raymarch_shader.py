# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Headless smoke checks for the assembled SDF raymarch shader (Phases 2/5).

The real GLSL compile check needs a WebGL2 context (exercised in the browser
during Phases 6/6a). These tests catch the structural/assembly errors early:
the concatenation order, the single ``main()``, the absence of stray
``#version``/``precision`` directives (three.js prepends them for a
``GLSL3`` ShaderMaterial), missing function definitions, the injected
`map`/`materialColor` contract, and brace balance.
"""

from __future__ import annotations

from pathlib import Path

SDC_DIR = Path(__file__).parents[3] / "pytanga" / "viz" / "templates" / "sdf"

SHADER_DIR = SDC_DIR / "shaders"
LIB_FILES = ["sdf_common.glsl", "primitives.glsl", "combinators.glsl"]
RAYMARCH_FILE = "raymarch.glsl"


def _read(name: str) -> str:
    return (SHADER_DIR / name).read_text(encoding="utf-8")


def _brace_balance(src: str) -> int:
    depth = 0
    for ch in src:
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth < 0:
                return depth
    return depth


# ── Assembly order ──────────────────────────────────────────


def test_library_files_exist() -> None:
    for name in LIB_FILES + [RAYMARCH_FILE]:
        assert (SHADER_DIR / name).is_file(), f"missing {name}"


def test_library_sources_have_no_main() -> None:
    for name in LIB_FILES:
        assert "void main" not in _read(name), f"{name} must not define main()"


def test_raymarch_has_exactly_one_main() -> None:
    assert _read(RAYMARCH_FILE).count("void main") == 1


def test_no_version_or_precision_directives() -> None:
    # three.js prepends `#version 300 es` + `precision highp float;` for a
    # GLSL3 ShaderMaterial; the concatenated sources must not duplicate them.
    for name in LIB_FILES + [RAYMARCH_FILE]:
        for line in _read(name).splitlines():
            stripped = line.lstrip()
            assert not stripped.startswith("#version"), (
                f"{name} must not set #version"
            )
            assert not stripped.startswith("precision"), (
                f"{name} must not set precision"
            )


def test_combined_fragment_is_brace_balanced() -> None:
    combined = "\n".join(_read(n) for n in LIB_FILES + [RAYMARCH_FILE])
    assert _brace_balance(combined) == 0


def test_primitive_functions_present_in_assembly() -> None:
    primitives = _read("primitives.glsl")
    combined = "\n".join(_read(n) for n in LIB_FILES + [RAYMARCH_FILE])
    used = {
        "sdSphere",
        "sdEllipsoid",
        "sdBox",
        "sdRoundBox",
        "sdPlane",
        "sdSegment",
        "sdCapsule",
        "sdCylinder",
        "sdCappedCylinder",
        "sdCone",
        "sdCappedCone",
        "sdTorus",
        "opUnion",
        "opSubtract",
        "opIntersect",
        "opSmoothUnion",
        "opSmoothSubtract",
        "opSmoothIntersect",
    }
    for fn in used:
        assert fn in primitives or fn in combined, f"{fn} definition missing"


def test_raymarch_map_and_material_contract() -> None:
    body = _read(RAYMARCH_FILE)
    # `map(p)` is injected by the host (composer / algebra evaluator), never
    # defined in the body; the body must NOT define it, only call it. Examine
    # only code lines (ignore the contract comment).
    code_lines = [ln for ln in body.splitlines() if not ln.strip().startswith("//")]
    code = "\n".join(code_lines)
    assert ".x" in code and "map(p" in code, "raymarch body must call map(p)"
    assert "vec2 map(" not in code, "raymarch body must not define map"
    # `materialColor` is injected by the material table.
    assert "materialColor(" in code
    # The body must define its own helpers.
    for symbol in ("opacityOf", "calcNormal", "softShadow", "shade"):
        assert f"{symbol}(" in code, f"raymarch body must define {symbol}"


def test_material_table_and_composer_exist() -> None:
    composer = (SDC_DIR / "composer.js").read_text(encoding="utf-8")
    material = (SDC_DIR / "material-table.js").read_text(encoding="utf-8")
    assert "composeObjects" in composer
    assert "materialColor" in material and "materialPreamble" in material