# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Standard surface shaders.

Each factory returns a :class:`~pytanga.viz.surface.SurfaceShader` whose
fragment defines ``vec3 surfaceColor(vec3 baseColor, vec3 n, vec3 p)`` and shades
through the host-provided ``tangaLight(...)`` helper (ambient + directional
diffuse from the scene's global lighting).  The returned ``uniforms`` dict holds
the runtime values for the fragment's declared uniforms.
"""

from __future__ import annotations

from .material import SurfaceShader


def _hex_rgb(value: str) -> list[float]:
    """Convert ``#RRGGBB`` (or ``RRGGBB``) to an ``[r, g, b]`` float triple."""
    raw = value.lstrip("#")
    if len(raw) != 6:
        raise ValueError(f"expected a #RRGGBB color, got {value!r}")
    return [int(raw[i : i + 2], 16) / 255.0 for i in (0, 2, 4)]


def checkerboard(
    color_a: str = "#ffffff",
    color_b: str = "#000000",
    scale: float = 8.0,
) -> SurfaceShader:
    """A UV checkerboard pattern (``scale`` cells along each axis)."""
    fragment = """
uniform vec3 u_color_a;
uniform vec3 u_color_b;
uniform float u_scale;

vec3 surfaceColor(vec3 baseColor, vec3 n, vec3 p) {
    vec2 c = floor(vUv * u_scale);
    float k = mod(c.x + c.y, 2.0);
    vec3 albedo = mix(u_color_a, u_color_b, k);
    return tangaLight(albedo, n, p);
}
"""
    return SurfaceShader(
        "checkerboard",
        fragment,
        uniforms={
            "u_color_a": _hex_rgb(color_a),
            "u_color_b": _hex_rgb(color_b),
            "u_scale": float(scale),
        },
    )


def sphere_coloring() -> SurfaceShader:
    """Color a surface by its normalized local position (a sphere's \"coloring\")."""
    fragment = """
vec3 surfaceColor(vec3 baseColor, vec3 n, vec3 p) {
    vec3 albedo = normalize(vLocalPos) * 0.5 + 0.5;
    return tangaLight(albedo, n, p);
}
"""
    return SurfaceShader("sphere_coloring", fragment)


def grid(
    line_color: str = "#000000",
    background: str = "#ffffff",
    scale: float = 8.0,
    line_width: float = 0.05,
) -> SurfaceShader:
    """A UV grid pattern with antialiased lines."""
    fragment = """
uniform vec3 u_line_color;
uniform vec3 u_background;
uniform float u_scale;
uniform float u_line_width;

vec3 surfaceColor(vec3 baseColor, vec3 n, vec3 p) {
    vec2 uv = vUv * u_scale;
    vec2 g = abs(fract(uv - 0.5) - 0.5) / fwidth(uv);
    float line = min(g.x, g.y);
    float k = 1.0 - smoothstep(u_line_width, u_line_width + 0.5, line);
    vec3 albedo = mix(u_background, u_line_color, k);
    return tangaLight(albedo, n, p);
}
"""
    return SurfaceShader(
        "grid",
        fragment,
        uniforms={
            "u_line_color": _hex_rgb(line_color),
            "u_background": _hex_rgb(background),
            "u_scale": float(scale),
            "u_line_width": float(line_width),
        },
    )


def gradient(
    color_a: str = "#ff0000",
    color_b: str = "#0000ff",
    axis: str = "u",
) -> SurfaceShader:
    """A linear gradient along the U or V texture axis."""
    if axis not in ("u", "v"):
        raise ValueError(f"axis must be 'u' or 'v', got {axis!r}")
    coord = "vUv.x" if axis == "u" else "vUv.y"
    fragment = f"""
uniform vec3 u_color_a;
uniform vec3 u_color_b;

vec3 surfaceColor(vec3 baseColor, vec3 n, vec3 p) {{
    vec3 albedo = mix(u_color_a, u_color_b, {coord});
    return tangaLight(albedo, n, p);
}}
"""
    return SurfaceShader(
        "gradient",
        fragment,
        uniforms={
            "u_color_a": _hex_rgb(color_a),
            "u_color_b": _hex_rgb(color_b),
        },
    )
