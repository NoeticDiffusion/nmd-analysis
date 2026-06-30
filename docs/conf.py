"""Sphinx configuration for the nmd-analysis documentation."""

from __future__ import annotations

import os
import sys
from pathlib import Path

DOCS_DIR = Path(__file__).parent.resolve()
PKG_DIR = DOCS_DIR.parent / "nmd-analysis"
sys.path.insert(0, str(PKG_DIR))

# -- Project information -----------------------------------------------------

project = "nmd-analysis"
author = "nmd-analysis contributors"
copyright = "2026, nmd-analysis contributors"

# The full version, including alpha/beta/rc tags.
release = "0.1.0"

# -- General configuration ---------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "myst_parser",
]

# Map source suffixes: .rst is default; .md handled by myst_parser.
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# Markdown: enable MyST extensions used in the docs.
myst_enable_extensions = [
    "dollarmath",
    "amsmath",
    "colon_fence",
    "deflist",
    "html_admonition",
    "linkify",
    "substitution",
    "tasklist",
]
myst_heading_anchors = 3

# -- Autodoc -----------------------------------------------------------------

autodoc_default_options = {
    "show-inheritance": True,
    "member-order": "bysource",
}
autodoc_typehints = "description"
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
    "pandas": ("https://pandas.pydata.org/pandas-docs/stable/", None),
}

# -- HTML output -------------------------------------------------------------

html_theme = "furo"
html_static_path = ["_static"]
html_title = "nmd-analysis"
html_baseurl = "https://nmd-analysis.readthedocs.io/"
