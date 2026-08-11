# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Dict-like wrapper that normalises class keys to their ``__name__``.

Also contains factory functions for creating default style instances
and helpers for resolving style priorities.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ._styles import AnnotationStyle, FigureStyle, LabelStyle


class _StyleDict:
    """Dict-like wrapper that normalises class keys to their ``__name__``.

    Wraps an internal ``dict[str, VizStyle]`` so users can look up and
    modify default styles using either string keys (``"Sphere"``) or the
    class itself (``Sphere``).  Both forms read from and write to the
    same underlying dictionary.

    Usage::

        styles = _StyleDict(internal_dict)
        styles[Point] = PointStyle(size=0.25)   # writes to "Point"
        styles[Point]   # reads from "Point"
        styles["Point"] # same
    """

    def __init__(self, mapping: dict[str, Any]) -> None:
        self._mapping = mapping

    @staticmethod
    def _key(k: str | type) -> str:
        return k.__name__ if isinstance(k, type) else k

    def __getitem__(self, k: str | type) -> Any:
        return self._mapping[self._key(k)]

    def __setitem__(self, k: str | type, v: Any) -> None:
        self._mapping[self._key(k)] = v

    def __delitem__(self, k: str | type) -> None:
        del self._mapping[self._key(k)]

    def __contains__(self, k: str | type) -> bool:
        return self._key(k) in self._mapping

    def __iter__(self):
        return iter(self._mapping)

    def __len__(self) -> int:
        return len(self._mapping)

    def keys(self):
        return self._mapping.keys()

    def values(self):
        return self._mapping.values()

    def items(self):
        return self._mapping.items()

    def get(self, k: str | type, default: Any = None) -> Any:
        return self._mapping.get(self._key(k), default)

    def __repr__(self) -> str:
        return f"_StyleDict({self._mapping!r})"


def _make_default_styles() -> _StyleDict:
    """Return independent copies of the per-kind default style instances.

    Each ``Visualizer`` instance gets its own copies so that mutations
    to one visualizer's default styles don't affect another.
    """
    from copy import copy

    from ._styles import _DEFAULT_STYLE_FOR_KIND as _SRC

    return _StyleDict({k: copy(v) for k, v in _SRC.items()})


# ── Factory functions for default style instances ───────────────


def _make_default_label_style() -> "LabelStyle":
    """Return a fully-initialised canonical ``LabelStyle``."""
    from ._styles import LabelStyle as _LS

    return _LS(
        font_size=14,
        font_family="sans-serif",
        color="#ffffff",
        background="rgba(0, 0, 0, 0.6)",
        offset_local=(0.0, 0.0, 0.0),
        offset_2d=(0.0, 0.0),
        align=(0.5, 0.5),
    )


def _make_default_annotation_style() -> "AnnotationStyle":
    """Return a fully-initialised canonical ``AnnotationStyle``."""
    from ._styles import AnnotationStyle as _AS

    return _AS(
        width="100%",
        max_width="800px",
        max_height="250px",
        font_size=13,
        font_family="sans-serif",
        color="#cccccc",
        background="rgba(0, 0, 0, 0.75)",
        link_color="#88ccff",
        code_background="rgba(255, 255, 255, 0.1)",
        padding="10px 16px",
        border_radius="4px",
    )


def _make_default_label_styles() -> dict[str, "LabelStyle | None"]:
    """Return the per-kind label style overrides dict (all ``None`` initially)."""
    return {
        "Point": None,
        "Direction": None,
        "HPoint": None,
        "PointPair": None,
        "ImagPointPair": None,
        "Line": None,
        "Plane": None,
        "Circle": None,
        "ImagCircle": None,
        "Sphere": None,
        "ImagSphere": None,
        "Space": None,
        "ReflectionLine": None,
        "ReflectionPlane": None,
        "ReflectionPoint": None,
        "Inversion": None,
        "Rotor": None,
        "Translator": None,
        "Dilator": None,
        "Motor": None,
        "GeneralRotor": None,
        "PointPath": None,
    }


# ── Kind-key mapping ───────────────────────────────────────────


def _kind_to_key(kind: str) -> str:
    """Map a lower-case kind string to the key used in ``_DEFAULT_STYLE_FOR_KIND``."""
    mapping = {
        "point": "Point",
        "direction": "Direction",
        "hpoint": "HPoint",
        "point_pair": "PointPair",
        "imagpointpair": "ImagPointPair",
        "line": "Line",
        "plane": "Plane",
        "circle": "Circle",
        "imagcircle": "ImagCircle",
        "sphere": "Sphere",
        "imagsphere": "ImagSphere",
        "space": "Space",
        "reflection_line": "ReflectionLine",
        "reflection_plane": "ReflectionPlane",
        "reflection_origin": "ReflectionPoint",
        "inversion": "Inversion",
        "rotor": "Rotor",
        "translator": "Translator",
        "dilator": "Dilator",
        "motor": "Motor",
        "general_rotor": "GeneralRotor",
        "pointpath": "PointPath",
    }
    key = mapping.get(kind.lower())
    if key is None:
        raise ValueError(f"Unknown entity kind: {kind!r}")
    return key


# ── Style-resolution helpers ───────────────────────────────────


def _resolve_label_style(
    global_default: "LabelStyle",
    per_kind: "LabelStyle | None",
    user_style: "LabelStyle",
) -> "LabelStyle":
    """Resolve the effective label style: user > per-kind > global.

    All three inputs are ``LabelStyle`` instances.  Fields from the
    higher-priority source overwrite lower-priority ones only if they
    are not ``None``.
    """
    from copy import copy

    # Start with a copy of the global default
    result = copy(global_default)

    # Overlay per-kind (non-None fields only)
    if per_kind is not None:
        for field_name, value in per_kind.__dict__.items():
            if value is not None:
                setattr(result, field_name, value)

    # Overlay user (non-None fields only)
    for field_name, value in user_style.__dict__.items():
        if value is not None:
            setattr(result, field_name, value)

    return result


def _resolve_annotation_style(
    canonical: "AnnotationStyle",
    user_style: "AnnotationStyle | None",
) -> dict[str, Any]:
    """Merge user-supplied annotation style with the canonical default.

    Returns a dict suitable for JSON serialization.  Only fields the
    user explicitly set (non-``None``) override the canonical defaults.
    """
    if user_style is None:
        return canonical.to_dict()

    canonical_dict = canonical.to_dict()
    user_dict = user_style.to_dict()
    merged = dict(canonical_dict)
    for k, v in user_dict.items():
        if v is not None:
            merged[k] = v
    return merged


def _resolve_figure_style(
    canonical: "FigureStyle",
    user_style: "FigureStyle | None",
) -> dict[str, Any]:
    """Merge user-supplied figure style with the canonical default."""
    if user_style is None:
        return canonical.to_dict()

    canonical_dict = canonical.to_dict()
    user_dict = user_style.to_dict()
    merged = dict(canonical_dict)
    for k, v in user_dict.items():
        if v is not None:
            merged[k] = v
    return merged


# ── Texture label style defaults ────────────────────────────────


def _make_default_tex_label_style() -> "TextureLabelStyle":
    """Return a fully-initialised canonical ``TextureLabelStyle``."""
    from ._styles import TextureLabelStyle as _TLS

    return _TLS(
        font_size=48,
        color="#000000",
        background=None,
        resolution=1024,
    )


def _make_default_tex_label_styles() -> dict[str, "TextureLabelStyle | None"]:
    """Return per-kind texture label style overrides.

    Sphere defaults ``offset_v=0.25`` to center at the equator.
    Plane defaults ``offset_v=0.0``.  All other kinds default to ``None``
    (no texture label).
    """
    from ._styles import TextureLabelStyle as _TLS

    return {
        "Sphere": _TLS(repeat_u=2, repeat_v=1, offset_v=0.0, aspect=1.0, scale=0.8),
        "Plane": _TLS(offset_v=0.0),
        "Point": None,
        "Direction": None,
        "HPoint": None,
        "PointPair": None,
        "ImagPointPair": None,
        "Line": None,
        "Circle": None,
        "ImagCircle": None,
        "ImagSphere": None,
        "Space": None,
        "ReflectionLine": None,
        "ReflectionPlane": None,
        "ReflectionPoint": None,
        "Inversion": None,
        "Rotor": None,
        "Translator": None,
        "Dilator": None,
        "Motor": None,
        "GeneralRotor": None,
        "PointPath": None,
    }


def _resolve_tex_label_style(
    global_default: "TextureLabelStyle",
    per_kind: "TextureLabelStyle | None",
    user_style: "TextureLabelStyle",
) -> "TextureLabelStyle":
    """Resolve the effective texture label style: user > per-kind > global.

    All three inputs are ``TextureLabelStyle`` instances.  Fields from the
    higher-priority source overwrite lower-priority ones only if they
    are not ``None``.
    """
    from copy import copy

    # Start with a copy of the global default
    result = copy(global_default)

    # Overlay per-kind (non-None fields only)
    if per_kind is not None:
        for field_name, value in per_kind.__dict__.items():
            if value is not None:
                setattr(result, field_name, value)

    # Overlay user (non-None fields only)
    for field_name, value in user_style.__dict__.items():
        if value is not None:
            setattr(result, field_name, value)

    return result
