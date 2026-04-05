Configuration
=============

Kubernetes Access
-----------------

The MCP server requires access to a Kubernetes cluster with Kubeflow Training Operator.

**Kubeconfig locations (in order of precedence):**

1. ``KUBECONFIG`` environment variable
2. ``~/.kube/config`` (default)

.. code-block:: bash

   # Verify cluster access
   kubectl get nodes
   kubectl get clustertrainingruntimes

**Container/Docker deployments:**

Mount your kubeconfig when running in containers:

.. code-block:: bash

   docker run -v ~/.kube:/root/.kube:ro kubeflow-mcp serve

Or set in MCP client config:

.. code-block:: json

   {
     "mcpServers": {
       "kubeflow": {
         "command": "kubeflow-mcp",
         "args": ["serve"],
         "env": {
           "KUBECONFIG": "/path/to/kubeconfig"
         }
       }
     }
   }

Config File
-----------

``~/.kf-mcp.yaml``:

.. code-block:: yaml

   default_namespace: kubeflow
   default_runtime: torch-tune
   log_level: INFO

Policy File
-----------

``~/.kf-mcp-policy.yaml``:

.. code-block:: yaml

   personas:
     viewer:
       allowed_tools: [list_training_jobs, get_training_job, get_training_logs]
       allowed_namespaces: [default, kubeflow]
     developer:
       allowed_tools: ["*"]
       denied_tools: [delete_training_job]

   policy:
     default_persona: developer
     require_confirmation: true

Environment Variables
---------------------

.. list-table::
   :widths: 40 20 40
   :header-rows: 1

   * - Variable
     - Default
     - Description
   * - ``KUBECONFIG``
     - ``~/.kube/config``
     - Path to kubeconfig file
   * - ``KUBEFLOW_MCP_NAMESPACE``
     - ``default``
     - Default Kubernetes namespace
   * - ``KUBEFLOW_MCP_LOG_LEVEL``
     - ``INFO``
     - Log verbosity (DEBUG, INFO, WARNING, ERROR)

CLI Options
-----------

.. code-block:: bash

   kubeflow-mcp serve \
     --persona ml-engineer \
     --transport stdio \
     --log-level INFO

.. list-table::
   :widths: 25 25 50
   :header-rows: 1

   * - Option
     - Default
     - Description
   * - ``--persona``
     - ``ml-engineer``
     - User role for tool filtering
   * - ``--transport``
     - ``stdio``
     - MCP transport (stdio, sse)
   * - ``--log-level``
     - ``INFO``
     - Log verbosity

Next: :doc:`../guide/tools` | :doc:`../guide/agents`
