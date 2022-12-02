#!/usr/bin/env python
from datetime import datetime

import twister2  # noqa: E402

# needs_sphinx = '1.0'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx_autodoc_typehints',
    'sphinx.ext.viewcode',
    'sphinx.ext.intersphinx',
    'sphinx_rtd_theme',
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
source_suffix = ['.rst']

# The master toctree document.
master_doc = 'index'

# General information about the project.
project = 'pytest-twister'
copyright = f'2022-{datetime.now().year}, Zephyr'
author = 'Zephyr'

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
html_static_path = ['_static']

autosummary_generate = True

autoapi_type = 'python'
autoapi_dirs = ['../src/twister2']

intersphinx_mapping = {
    'python': ('https://docs.python.org/3.11/', None),
    'pytest': ('https://docs.pytest.org/en/latest/', None),
    'marshmallow': ('https://marshmallow.readthedocs.io/en/latest/', None),
}
