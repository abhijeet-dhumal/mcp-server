# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys

# Add the project root to the path for autodoc
sys.path.insert(0, os.path.abspath("../.."))
sys.path.insert(0, os.path.abspath("../../src"))

# -- Project information -----------------------------------------------------
project = "Kubeflow MCP Server"
copyright = "2024, The Kubeflow Authors"
author = "The Kubeflow Authors"

# Version is read from kubeflow_mcp package
try:
    from kubeflow_mcp import __version__ as version
except ImportError:
    version = "0.1.0-dev"

release = version

# -- General configuration ---------------------------------------------------
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx_autodoc_typehints",
    "sphinx_copybutton",
    "sphinx_design",
    "myst_parser",
    "sphinxcontrib.mermaid",
]

# Templates path
templates_path = ["_templates"]

# Patterns to exclude
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# Source file suffixes (support both RST and Markdown)
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

# The master toctree document
master_doc = "index"

# -- Options for autodoc -----------------------------------------------------
autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    "undoc-members": False,
    "exclude-members": "__weakref__,__init__",
    "show-inheritance": True,
}

# Generate autosummary pages automatically
autosummary_generate = True
autosummary_imported_members = True

# Napoleon settings (for Google-style docstrings)
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = True
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_type_aliases = None

# Type hints settings - show types in signature
autodoc_typehints = "signature"
typehints_use_signature = True
typehints_use_signature_return = True
typehints_fully_qualified = False
always_document_param_types = False
typehints_document_rtype = False

# -- Options for HTML output -------------------------------------------------
html_theme = "furo"
html_title = "Kubeflow MCP Server"
html_static_path = ["_static"]
html_css_files = ["custom.css"]

# Furo theme options
html_theme_options = {
    "sidebar_hide_name": False,
    "navigation_with_keys": True,
    "top_of_page_buttons": ["view", "edit"],
    "source_repository": "https://github.com/kubeflow/mcp-server",
    "source_branch": "main",
    "source_directory": "docs/source/",
    "announcement": """
        <nav class="top-nav">
            <a href="/index.html" class="top-nav-brand">
                <span>Kubeflow MCP Server</span>
            </a>
            <div class="top-nav-links">
                <a href="https://github.com/kubeflow/mcp-server">GitHub</a>
                <a href="https://www.kubeflow.org/docs/about/community/#slack-channels">Slack</a>
            </div>
        </nav>
    """,
}

# -- Options for intersphinx -------------------------------------------------
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "kubernetes": ("https://kubernetes.readthedocs.io/en/latest/", None),
}

# -- Options for copybutton --------------------------------------------------
copybutton_prompt_text = r">>> |\.\.\. |\$ |In \[\d*\]: | {2,5}\.\.\.: "
copybutton_prompt_is_regexp = True

# -- MyST Parser options -----------------------------------------------------
myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "fieldlist",
    "tasklist",
]
myst_heading_anchors = 3

# -- Options for search ------------------------------------------------------
html_search_language = "en"
html_search_options = {
    "type": "default",
    "tokenizer_lang": "porter",
}
