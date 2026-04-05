Configuration
=============

The Kubeflow MCP Server can be configured through YAML files and environment variables.

Configuration File
------------------

Create ``~/.kf-mcp.yaml``:

.. code-block:: yaml

   # Default namespace for training jobs
   default_namespace: kubeflow

   # Default training runtime
   default_runtime: torch-tune

   # Kubernetes configuration
   kubeconfig: ~/.kube/config

   # Logging level
   log_level: INFO

Policy File
-----------

Create ``~/.kf-mcp-policy.yaml`` for access control:

.. code-block:: yaml

   # Custom personas
   personas:
     viewer:
       description: "Read-only access"
       allowed_tools:
         - list_training_jobs
         - get_training_job
         - get_training_logs
         - get_training_events
       denied_tools: []
       allowed_namespaces:
         - default
         - kubeflow

     developer:
       description: "Full training access"
       allowed_tools: ["*"]
       denied_tools:
         - delete_training_job
       allowed_namespaces:
         - dev-*

   # Global policy
   policy:
     default_persona: developer
     require_confirmation: true
     read_only: false

Environment Variables
---------------------

.. list-table::
   :header-rows: 1
   :widths: 30 20 50

   * - Variable
     - Default
     - Description
   * - ``KUBEFLOW_MCP_NAMESPACE``
     - ``default``
     - Default namespace for operations
   * - ``KUBEFLOW_MCP_RUNTIME``
     - ``torch-tune``
     - Default training runtime
   * - ``KUBEFLOW_MCP_LOG_LEVEL``
     - ``INFO``
     - Logging verbosity
   * - ``KUBECONFIG``
     - ``~/.kube/config``
     - Kubernetes config path

CLI Options
-----------

.. code-block:: bash

   kubeflow-mcp serve --help

   Options:
     --clients, -c TEXT      Comma-separated client modules (trainer, optimizer, hub)
     --persona, -p TEXT      Persona for tool filtering (readonly, data-scientist, ml-engineer, platform-admin)
     --transport, -t TEXT    MCP transport protocol (stdio, http)
     --log-level, -l TEXT    Log level (DEBUG, INFO, WARNING, ERROR)
     --log-format TEXT       Log format (json, console)
     --help                  Show this message and exit

Next Steps
----------

- :doc:`../guide/tools` - Explore available tools
- :doc:`../guide/agents` - Set up the local agent
