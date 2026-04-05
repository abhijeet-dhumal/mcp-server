Installation
============

Requirements
------------

- Python 3.10 or higher
- Access to a Kubernetes cluster with Kubeflow Training Operator installed
- kubectl configured with cluster access

Install from PyPI
-----------------

.. code-block:: bash

   pip install kubeflow-mcp

Install with Extras
-------------------

For local agent support:

.. code-block:: bash

   pip install kubeflow-mcp[agents]

For development:

.. code-block:: bash

   pip install kubeflow-mcp[dev]

Install from Source
-------------------

.. code-block:: bash

   git clone https://github.com/kubeflow/mcp-server.git
   cd mcp-server
   pip install -e ".[dev]"

Verify Installation
-------------------

.. code-block:: bash

   kubeflow-mcp --version
   kubeflow-mcp serve --help

Next Steps
----------

- :doc:`quickstart` - Get started with your first training job
- :doc:`configuration` - Configure the server for your environment
