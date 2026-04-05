Troubleshooting
===============

Common issues and solutions.

Connection Issues
-----------------

**Server not starting**

.. code-block:: bash

   # Check if installed correctly
   kubeflow-mcp --version
   
   # Verify Kubernetes access
   kubectl get nodes

**Client not connecting**

- Restart your MCP client after config changes
- Check config file path and JSON syntax
- Verify ``kubeflow-mcp`` is in PATH

Training Issues
---------------

**"Runtime not found"**

.. code-block:: text

   "List available runtimes in my cluster"

The runtime name must match an installed ClusterTrainingRuntime.

**Job stuck in Pending**

.. code-block:: text

   "Show events for my training job"

Common causes:

- Insufficient GPU resources
- Node selector not matching any nodes
- PVC not bound

**OOMKilled errors**

Reduce batch size or use a smaller model:

.. code-block:: text

   "Estimate resources for google/gemma-2b with batch size 2"

GPU Issues
----------

**No GPUs detected**

.. code-block:: text

   "What GPU resources are available?"

If ``gpu_total=0``:

- Verify NVIDIA device plugin is installed
- Check node labels and taints
- Ensure GPU nodes are schedulable

**GPU memory exceeded**

Use ``estimate_resources`` before training to verify requirements.

Getting Help
------------

- Check logs: ``kubeflow-mcp serve --log-level DEBUG``
- `GitHub Issues <https://github.com/kubeflow/mcp-server/issues>`_
- `#kubeflow-ml-experience <https://www.kubeflow.org/docs/about/community/#slack-channels>`_ on Slack
