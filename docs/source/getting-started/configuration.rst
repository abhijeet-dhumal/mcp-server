Configuration
=============

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

Environment
-----------

.. list-table::
   :widths: 40 20 40

   * - Variable
     - Default
     - Description
   * - ``KUBEFLOW_MCP_NAMESPACE``
     - ``default``
     - Default namespace
   * - ``KUBEFLOW_MCP_LOG_LEVEL``
     - ``INFO``
     - Log verbosity

CLI Options
-----------

.. code-block:: bash

   kubeflow-mcp serve \
     --persona ml-engineer \
     --transport stdio \
     --log-level INFO

Next: :doc:`../guide/tools` | :doc:`../guide/agents`
