Installation
============

Requirements
------------

- Python 3.10+
- Kubernetes cluster with Kubeflow Training Operator
- kubectl configured

Install
-------

.. code-block:: bash

   pip install kubeflow-mcp

With extras:

.. code-block:: bash

   pip install kubeflow-mcp[agents]  # Local Ollama agent
   pip install kubeflow-mcp[dev]     # Development tools

From source:

.. code-block:: bash

   git clone https://github.com/kubeflow/mcp-server.git
   cd mcp-server && pip install -e ".[dev]"

Verify
------

.. code-block:: bash

   kubeflow-mcp --version
   kubeflow-mcp serve --help

Next: :doc:`quickstart` | :doc:`configuration`
