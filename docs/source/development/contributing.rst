Contributing
============

Thank you for your interest in contributing to the Kubeflow MCP Server!

For detailed contribution guidelines, see the
`CONTRIBUTING.md <https://github.com/kubeflow/mcp-server/blob/main/CONTRIBUTING.md>`_
file in the repository.

Quick Start
-----------

1. Fork and clone the repository
2. Install development dependencies:

   .. code-block:: bash

      pip install -e ".[dev]"

3. Run tests:

   .. code-block:: bash

      make test

4. Run linting:

   .. code-block:: bash

      make lint

5. Submit a pull request

Code Style
----------

- Follow PEP 8 guidelines
- Use Google-style docstrings
- Format with ``ruff format``
- Type hints required for public APIs

Testing
-------

.. code-block:: bash

   # Run all tests
   make test

   # Run with coverage
   make test-cov

   # Run specific test
   pytest tests/test_tools.py -v

Documentation
-------------

Build the docs locally:

.. code-block:: bash

   make docs

   # Serve locally
   make docs-serve

Community
---------

- `Slack <https://www.kubeflow.org/docs/about/community/#slack-channels>`_ - #kubeflow-ml-experience
- `GitHub Discussions <https://github.com/kubeflow/mcp-server/discussions>`_
- `Community Meetings <https://www.kubeflow.org/docs/about/community/>`_
