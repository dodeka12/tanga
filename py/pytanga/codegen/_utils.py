# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Template-substitution helpers for code generation."""

import re


def sub_braced(template: str, name: str, replacement: str) -> str:
    """Replace {NAME} with optional whitespace inside braces (e.g. { NAME })."""
    return re.sub(
        r"\{\s*" + re.escape(name) + r"\s*\}",
        replacement,
        template,
    )


def sub_bare(template: str, name: str, replacement: str) -> str:
    """Replace bare-word placeholder matching whole-word only."""
    return re.sub(
        r"\b" + re.escape(name) + r"\b",
        replacement,
        template,
    )
