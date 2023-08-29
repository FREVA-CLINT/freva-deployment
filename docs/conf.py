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
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "nbsphinx",
    "recommonmark",
    "sphinx.ext.viewcode",
    "sphinxcontrib_github_alt",
    "sphinx_copybutton",
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
html_logo = "freva_owl.svg"
html_favicon = "freva_owl.svg"
# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]
html_theme_options = {
    "icon_links": [
        {
            "name": "GitHub",
            "url": "https://github.com/FREVA-CLINT/freva-deployment",
            "icon": "fa-brands fa-github",
        }
    ],
    "navigation_with_keys": True,
    "collapse_navigation": False,
    "top_of_page_button": "edit",
    "navigation_depth": 4,
    "navbar_align": "left",
    "show_nav_level": 2,
    "navigation_depth": 4,
    #    "primary_sidebar_end": ["indices.html", "sidebar-ethical-ads.html"],
    "navbar_center": ["navbar-nav"],
    "secondary_sidebar_items": ["page-toc"],
    "light_css_variables": {
        "color-brand-primary": "tomato",
    },
}
html_context = {
    "github_user": "FREVA-CLINT",
    "github_repo": "freva",
    "github_version": "main",
    "doc_path": "docs",
}
# html_sidebars = {
#    "**": [
#        "search-field.html",
#        "sidebar-nav-bs.html",
#        "sidebar-ethical-ads.html",
#    ]
# }

source_parsers = {
    ".md": CommonMarkParser,
}

source_suffix = [".rst", ".md"]
