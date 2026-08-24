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


def test_raymarch_uses_glsl3_fragment_output() -> None:
    # GLSL ES 3.0 (WebGL2) has no legacy `gl_FragColor`; the fragment output
    # must be declared as an `out vec4` and assigned instead. Examine code
    # lines only so the explanatory comments do not trip the check.
    body = _read(RAYMARCH_FILE)
    code_lines = [ln for ln in body.splitlines() if not ln.strip().startswith("//")]
    code = "\n".join(code_lines)
    assert "out vec4" in code
    assert "gl_FragColor" not in code


def test_raymarch_ndc_uses_full_resolution() -> None:
    # The ray is reconstructed through the camera's inverse projection matrix,
    # which already applies the aspect ratio. NDC must therefore divide X and Y
    # independently (`/ uResolution`); dividing only by `uResolution.y` double-
    # scales X and stretches the render vertically.
    body = _read(RAYMARCH_FILE)
    assert "/ uResolution;" in body
    assert "/ uResolution.y" not in body


def test_raymarch_opacity_step_treats_hit_band_as_opaque() -> None:
    # The loop breaks on `d < SDF_EPSILON`, so at a hit the distance is a small
    # value within that band (usually slightly positive). The solid `step`
    # transfer must therefore use SDF_EPSILON, not `d < 0.0`, or every surface
    # shades to black. The `opacityOf` function is now emitted from
    # `algebra/opacities.js` (Phase 12), so the step stub lives there.
    opacities = (SDC_DIR / "algebra" / "opacities.js").read_text(encoding="utf-8")
    assert "return d < SDF_EPSILON ? epsilon : 0.0;" in opacities


def test_no_version_or_precision_directives() -> None:
    # three.js prepends `#version 300 es` + `precision highp float;` for a
    # GLSL3 ShaderMaterial; the concatenated sources must not duplicate them.
    for name in LIB_FILES + [RAYMARCH_FILE]:
        for line in _read(name).splitlines():
            stripped = line.lstrip()
            assert not stripped.startswith("#version"), f"{name} must not set #version"
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
    # `opacityOf` is a call site (the function is injected by the host from
    # `algebra/opacities.js`); the other helpers are defined in the body.
    assert "opacityOf(" in code
    for symbol in ("calcNormal", "softShadow", "shade"):
        assert f"{symbol}(" in code, f"raymarch body must define {symbol}"


def test_material_table_and_composer_exist() -> None:
    composer = (SDC_DIR / "composer.js").read_text(encoding="utf-8")
    material = (SDC_DIR / "material-table.js").read_text(encoding="utf-8")
    assert "composeObjects" in composer
    assert "materialColor" in material and "materialPreamble" in material


def test_volumetric_density_present() -> None:
    # The raymarch body defines the per-object volumetric density (exponential
    # Beer–Lambert falloff + hard cutoff) driven by the algebra uniforms.
    body = _read(RAYMARCH_FILE)
    assert "float mapDensity(" in body
    assert "u_ObjectParams[matId].z" in body
    assert "u_ObjectParams[matId].w" in body
    assert "exp(-d / falloff)" in body


def test_algebra_local_gradient_step() -> None:
    # The step rule is unconditional: `map(p)` carries the analytical gradient
    # norm (m.z), so the finite-difference `calcGradientNorm` and its per-object
    # analytic sentinel gate are gone.
    body = _read(RAYMARCH_FILE)
    assert "vec3 m = map(p);" in body
    assert "stepSize = d / max(m.z, 1.0);" in body
    assert "t += stepSize;" in body
    assert "calcGradientNorm" not in body
    assert "u_ObjectParams[matId].w > -0.5" not in body
