# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Bundled default style configuration for the Tanga 3D viewer.

:class:`VizStyleDefaults` groups all per-kind and global default style
instances into a single, deep-copyable object.  The :class:`Visualizer`
owns one canonical instance; each :class:`~pytanga.viz._scene.Scene`
receives an independent copy at creation so per-scene default changes never
leak back to the Visualizer.
"""

from __future__ import annotations

import copy as _copy
from dataclasses import dataclass
from typing import Any


@dataclass
class VizStyleDefaults:
    """Bundled default style configuration.

    Attributes:
        default_styles: Per-kind entity/operator style instances (a
            :class:`~pytanga.viz._style_dict._StyleDict`).
        default_label_style: Global default ``LabelStyle``.
        default_label_styles: Per-kind default label style overrides.
        default_annotation_style: Global default ``AnnotationStyle``.
        default_tex_label_style: Global default ``TextureLabelStyle``.
        default_tex_label_styles: Per-kind texture label style overrides.
    """

    default_styles: Any
    default_label_style: Any
    default_label_styles: Any
    default_annotation_style: Any
    default_tex_label_style: Any
    default_tex_label_styles: Any

    def copy(self) -> "VizStyleDefaults":
        """Return a deep copy of this configuration."""
        return VizStyleDefaults(
            default_styles=_copy.deepcopy(self.default_styles),
            default_label_style=_copy.deepcopy(self.default_label_style),
            default_label_styles=_copy.deepcopy(self.default_label_styles),
            default_annotation_style=_copy.deepcopy(self.default_annotation_style),
            default_tex_label_style=_copy.deepcopy(self.default_tex_label_style),
            default_tex_label_styles=_copy.deepcopy(self.default_tex_label_styles),
        )


def make_defaults() -> VizStyleDefaults:
    """Build a fresh canonical :class:`VizStyleDefaults` instance."""

    from ._style_dict import (
        _make_default_annotation_style,
        _make_default_label_style,
        _make_default_label_styles,
        _make_default_styles,
        _make_default_tex_label_style,
        _make_default_tex_label_styles,
    )

    return VizStyleDefaults(
        default_styles=_make_default_styles(),
        default_label_style=_make_default_label_style(),
        default_label_styles=_make_default_label_styles(),
        default_annotation_style=_make_default_annotation_style(),
        default_tex_label_style=_make_default_tex_label_style(),
        default_tex_label_styles=_make_default_tex_label_styles(),
    )