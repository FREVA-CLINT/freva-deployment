# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
from datetime import date

from recommonmark.parser import CommonMarkParser

sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath("../../src"))

from freva_deployment import __version__

# -- Project information -----------------------------------------------------

project = "freva-deployment"
copyright = f"{date.today().year}, DKRZ - CLINT"
author = "Climate Informatics and Technology"

# The full version, including alpha/beta/rc tags
release = __version__


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "recommonmark",
    "sphinx_copybutton",
    "sphinx_togglebutton",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "pydata_sphinx_theme"
html_logo = "_static/freva_owl.svg"
html_favicon = "_static/freva_owl.svg"
# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_sidebars = {"pagename": []}
html_static_path = ["_static"]
html_context = {
    "github_user": "FREVA-CLINT",
    "github_repo": "freva",
    "github_version": "main",
    "doc_path": "docs",
}
html_sidebars = {
    "community/index": [
        "sidebar-nav-bs",
        "custom-template",
    ],  # This ensures we test for custom sidebars
}

source_parsers = {
    ".md": CommonMarkParser,
}
html_theme_options = {
    "icon_links": [
        {
            "name": "GitHub",
            "url": "https://github.com/FREVA-CLINT/freva-deployment",
            "icon": "fa-brands fa-github",
        },
        {
            "name": "PyPI",
            "url": "https://pypi.org/project/freva-deployment",
            "icon": "fa-custom fa-pypi",
        },
    ],
    # "navbar_start": [],  # Remove navigation links from the top bar
    "navbar_center": [
        "navbar-nav"
    ],  # Add navigation links to the left sidebar
    "collapse_navigation": False,
    "navigation_depth": 4,
    "navbar_align": "left",
    "show_nav_level": 2,
    "secondary_sidebar_items": ["page-toc"],
}
html_sidebars = {"**": ["sidebar-nav-bs", "sidebar-ethical-ads"]}


source_suffix = [".rst", ".md"]


# -- MyST options ------------------------------------------------------------

# This allows us to use ::: to denote directives, useful for admonitions
myst_enable_extensions = ["colon_fence", "linkify", "substitution"]
myst_heading_anchors = 2
myst_substitutions = {
    "rtd": "[Read the Docs](https://readthedocs.org/)",
    "|version|": __version__,
}


# ReadTheDocs has its own way of generating sitemaps, etc.
if not os.environ.get("READTHEDOCS"):
    extensions += ["sphinx_sitemap"]

    html_baseurl = os.environ.get("SITEMAP_URL_BASE", "http://127.0.0.1:8000/")
    sitemap_locales = [None]
    sitemap_url_scheme = "{link}"

# specifying the natural language populates some key tags
language = "en"
