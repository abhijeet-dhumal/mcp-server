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

# Furo theme options with top navigation (matching SDK style)
html_theme_options = {
    "sidebar_hide_name": False,
    "navigation_with_keys": True,
    "top_of_page_buttons": ["view", "edit"],
    "source_repository": "https://github.com/kubeflow/mcp-server",
    "source_branch": "main",
    "source_directory": "docs/source/",
    # Top navigation bar with logo (same structure as SDK)
    "announcement": """
        <nav class="top-nav">
            <a href="/index.html" class="top-nav-brand">
                <svg class="top-nav-logo" width="28" height="28" viewBox="0 0 256 256" xmlns="http://www.w3.org/2000/svg">
                    <g transform="matrix(1.2742 0 0 1.2745 -46.441 11.393)">
                        <path d="m95.9 62.15 4.1 102.1 73.75-94.12a6.79 6.79 0 0 1 9.6-1.11l46 36.92-15-65.61z" fill="#4279f4"/>
                        <path d="m102.55 182.98h65.42l-40.17-32.23z" fill="#0028aa"/>
                        <path d="m180.18 83.92-44 56.14 46.88 37.61 44.47-55.76z" fill="#014bd1"/>
                        <path d="m83.56 52.3 0.01-0.01 38.69-48.52-62.39 30.05-15.41 67.51z" fill="#bedcff"/>
                        <path d="m45.32 122.05 41.44 51.96-3.95-98.98z" fill="#6ca1ff"/>
                        <path d="m202.31 28.73-59.66-28.73-37.13 46.56z" fill="#a1c3ff"/>
                    </g>
                </svg>
                <span>Kubeflow MCP Server</span>
            </a>
            <div class="top-nav-links">
                <a href="https://github.com/kubeflow/mcp-server">GitHub</a>
                <a href="https://www.kubeflow.org/docs/about/community/#slack-channels">Slack</a>
                <a href="https://www.kubeflow.org">Kubeflow</a>
            </div>
        </nav>
    """,
}

# Logo and favicon
html_logo = "_static/kubeflow-icon.svg"
html_favicon = "_static/kubeflow-icon.svg"

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

# -- Options for Mermaid diagrams --------------------------------------------
mermaid_version = "10.6.1"
mermaid_init_js = """
mermaid.initialize({
    startOnLoad: true,
    theme: 'default',
    themeVariables: {
        background: '#ffffff',
        primaryColor: '#dbeafe',
        primaryTextColor: '#1e3a5f',
        primaryBorderColor: '#3b82f6',
        lineColor: '#64748b',
        secondaryColor: '#f1f5f9',
        tertiaryColor: '#ffffff',
        textColor: '#1e293b',
        mainBkg: '#ffffff',
        nodeBorder: '#3b82f6',
        clusterBkg: '#f8fafc',
        clusterBorder: '#cbd5e1',
        titleColor: '#0f172a',
        edgeLabelBackground: '#ffffff',
        nodeTextColor: '#1e293b'
    }
});
"""
