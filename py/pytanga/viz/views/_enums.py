# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""String enums used by the layout view model."""

from __future__ import annotations

from enum import StrEnum


class EOrientation(StrEnum):
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"


class EStackDirection(StrEnum):
    VERTICAL = "vertical"
    HORIZONTAL = "horizontal"
    WRAP = "wrap"


class EStackAlign(StrEnum):
    START = "start"
    CENTER = "center"
    END = "end"
    STRETCH = "stretch"


class EStackJustify(StrEnum):
    START = "start"
    CENTER = "center"
    END = "end"
    SPACE_BETWEEN = "space-between"
    SPACE_AROUND = "space-around"
    SPACE_EVENLY = "space-evenly"
