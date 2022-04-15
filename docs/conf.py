#!/usr/bin/env python
import os
import sys
from datetime import datetime


sys.path.insert(0, os.path.abspath('..'))
sys.path.insert(1, os.path.abspath('../src/twister2'))

import twister2  # noqa: E402


# -- General configuration ---------------------------------------------

# needs_sphinx = '1.0'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx_autodoc_typehints',
    'sphinx.ext.viewcode',
    'sphinx.ext.intersphinx',
    'sphinx_rtd_theme',
    'm2r2',
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
source_suffix = ['.rst', '.md']

# The master toctree document.
master_doc = 'index'

# General information about the project.
project = 'pytest-twister'
copyright = f"2022-{datetime.now().year}, Zephyr"
author = "Zephyr"

# The version info for the project you're documenting, acts as replacement
# for |version| and |release|, also used in various other places throughout
# the built documents.
#
# The short X.Y version.
version = twister2.__version__
# The full version, including alpha/beta/rc tags.
release = twister2.__version__

# language = 'EN'

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This patterns also effect to html_static_path and html_extra_path
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'

# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = False


# -- Options for HTML output -------------------------------------------
html_favicon = '_static/favicon.png'
html_theme = 'sphinx_rtd_theme'

# Theme options are theme-specific and customize the look and feel of a
# theme further.  For a list of options available for each theme, see the
# documentation.
#
# html_theme_options = {}
html_static_path = ['_static']


# -- Options for HTMLHelp output ---------------------------------------

# Output file base name for HTML help builder.
htmlhelp_basename = 'twister2doc'

autosummary_generate = True

autoapi_type = 'python'
autoapi_dirs = ['../src/twister2']

intersphinx_mapping = {
    'python': ('https://docs.python.org/3.9/', None),
    'pytest': ('https://docs.pytest.org/en/latest/', None),
    'marshmallow': ('https://marshmallow.readthedocs.io/en/latest/', None),
}

nitpick_ignore = [
]
