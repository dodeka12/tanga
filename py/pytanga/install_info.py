# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Install packaged docs and examples with a single call."""

from pathlib import Path

from .install_docs import install_docs
from .install_examples import install_examples


def install_info() -> tuple[Path, Path]:
    """Install packaged docs and examples, back to back.

    Runs :func:`install_docs` then :func:`install_examples` and returns the two
    target directories as a ``(docs_dir, examples_dir)`` tuple.  This is a
    convenience wrapper so a single command mirrors both the packaged ``_docs/``
    and ``_examples/`` trees into ``.dep-docs/pytanga/`` and
    ``.dep-examples/pytanga/``.
    """
    docs_dir = install_docs()
    examples_dir = install_examples()
    return docs_dir, examples_dir
