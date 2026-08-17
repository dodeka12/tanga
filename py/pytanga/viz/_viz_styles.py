# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Style holder for the Tanga 3D viewer.

:class:`VizStyles` groups every changeable default-style bundle into a single,
deep-copyable object.  The :class:`~pytanga.viz.Visualizer` owns one master
instance (``global_styles``) and each :class:`~pytanga.viz._scene.Scene`
receives an independent deep copy (``styles``) so per-scene changes never leak
back to the master.
"""

from __future__ import annotations

import copy as _copy
from dataclasses import dataclass
from typing import Any

from ._style_dict import (
    _StyleDict,
    _make_default_act_point_style,
    _make_default_annotation_style,
    _make_default_label_style,
    _make_default_label_styles,
    _make_default_styles,
    _make_default_tex_label_style,
    _make_default_tex_label_styles,
)


@dataclass
class VizStyles:
    """Bundled default style configuration.

    Attributes:
        kind: Per-kind entity/operator style instances (a :class:`_StyleDict`),
            addressable by string key or class.  ``styles[kind] = ...`` sugar
            delegates here.
        label_base: Global default ``LabelStyle``.
        label_kind: Per-kind label style overrides (a :class:`_StyleDict`).
        annotation: Global default ``AnnotationStyle``.
        tex_label_base: Global default ``TextureLabelStyle``.
        tex_label_kind: Per-kind texture label style overrides (a
            :class:`_StyleDict`).
        act_point: Global default ``ActPointStyle``.
    """

    kind: _StyleDict
    label_base: Any
    label_kind: _StyleDict
    annotation: Any
    tex_label_base: Any
    tex_label_kind: _StyleDict
    act_point: Any

    def __getitem__(self, key: str | type) -> Any:
        """Return the entity/operator default style for *key* (``styles[kind]``)."""
        return self.kind[key]

    def __setitem__(self, key: str | type, value: Any) -> None:
        """Set the entity/operator default style for *key* (``styles[kind] = ...``)."""
        self.kind[key] = value

    def copy(self) -> "VizStyles":
        """Return a deep copy of this configuration."""
        return VizStyles(
            kind=_copy.deepcopy(self.kind),
            label_base=_copy.deepcopy(self.label_base),
            label_kind=_copy.deepcopy(self.label_kind),
            annotation=_copy.deepcopy(self.annotation),
            tex_label_base=_copy.deepcopy(self.tex_label_base),
            tex_label_kind=_copy.deepcopy(self.tex_label_kind),
            act_point=_copy.deepcopy(self.act_point),
        )


def make_styles() -> VizStyles:
    """Build a fresh canonical :class:`VizStyles` instance."""
    return VizStyles(
        kind=_make_default_styles(),
        label_base=_make_default_label_style(),
        label_kind=_StyleDict(_make_default_label_styles()),
        annotation=_make_default_annotation_style(),
        tex_label_base=_make_default_tex_label_style(),
        tex_label_kind=_StyleDict(_make_default_tex_label_styles()),
        act_point=_make_default_act_point_style(),
    )
