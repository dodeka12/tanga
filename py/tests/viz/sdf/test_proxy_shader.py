# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Headless smoke checks for the per-object SDF proxy shader (Phase 3).

Mirrors ``test_raymarch_shader.py``: the real GLSL compile needs a WebGL2
context (browser), so these tests catch structural errors early — the single
``main()``, the ``out vec4`` fragment output, the ``gl_FragDepth`` write, the
absence of stray ``#version``/``precision`` directives (three.js prepends them
for a ``GLSL3`` ShaderMaterial), and the injected single-object ``map``
contract.
"""

from __future__ import annotations

from pathlib import Path

RENDERS_DIR = (
    Path(__file__).parents[3] / "pytanga" / "viz" / "templates" / "renderers"
)
PROXY_FILE = RENDERS_DIR / "sdf" / "proxy.glsl"
GLSL_LIB = (
    Path(__file__).parents[3]
    / "pytanga"
    / "viz"
    / "templates"
    / "sdf"
    / "shaders"
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


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


def _code(src: str) -> str:
    return "\n".join(
        ln for ln in src.splitlines() if not ln.strip().startswith("//")
    )


def test_proxy_glsl_exists() -> None:
    assert PROXY_FILE.is_file()


def test_proxy_has_exactly_one_main() -> None:
    assert _read(PROXY_FILE).count("void main") == 1


def test_proxy_uses_glsl3_fragment_output() -> None:
    code = _code(_read(PROXY_FILE))
    assert "out vec4" in code
    assert "gl_FragColor" not in code


def test_proxy_writes_depth() -> None:
    assert "gl_FragDepth" in _read(PROXY_FILE)


def test_proxy_has_single_object_uniforms() -> None:
    body = _read(PROXY_FILE)
    for symbol in ("uMaterial", "uOpacity", "uMaxSteps", "uSoftShadows", "uBoundHalf"):
        assert symbol in body


def test_proxy_has_hover_glow_uniform() -> None:
    body = _read(PROXY_FILE)
    assert "uniform vec3 uHover" in body
    assert "col += uHover" in body


def test_proxy_no_version_or_precision() -> None:
    for line in _read(PROXY_FILE).splitlines():
        stripped = line.lstrip()
        assert not stripped.startswith("#version")
        assert not stripped.startswith("precision")


def test_proxy_map_contract() -> None:
    # `map(p)` is injected by the host (glsl.js), never defined in the body.
    code = _code(_read(PROXY_FILE))
    assert "map(p" in code, "proxy body must call map(p)"
    assert "float map(" not in code, "proxy body must not define map"


def test_proxy_is_brace_balanced() -> None:
    assert _brace_balance(_read(PROXY_FILE)) == 0


def test_proxy_shading_helpers_present() -> None:
    body = _read(PROXY_FILE)
    for symbol in ("calcNormal", "softShadow", "shade"):
        assert f"{symbol}(" in body


def test_proxy_has_edge_aa_fade() -> None:
    # Analytic silhouette AA: the march tracks the closest-approach distance and
    # fades the near-miss edge with a screen-space derivative + smoothstep.
    body = _read(PROXY_FILE)
    assert "dm.x < res" in body
    assert "tRes = t;" in body
    assert "dFdx(tRes)" in body and "dFdy(tRes)" in body
    assert "smoothstep(" in body
    assert "uAntialias" in body
    # The near-miss path shades the closest-approach point (no bright flat halo)
    # and still writes a (far) depth so the faint edge never occludes anything;
    # the hit path writes the real hit depth.
    assert "calcNormal(p0)" in body
    assert "gl_FragDepth = 1.0;" in body
    assert "gl_FragDepth = ndc * 0.5 + 0.5;" in body
