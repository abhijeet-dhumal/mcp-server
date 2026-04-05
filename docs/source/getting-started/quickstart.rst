Quick Start
===========

Connect an MCP client and run your first training job.

1. Start the Server
-------------------

**Option A: Local install**

.. code-block:: bash

   pip install kubeflow-mcp
   kubeflow-mcp serve

**Option B: Container**

.. code-block:: bash

   docker run -v ~/.kube:/root/.kube:ro ghcr.io/kubeflow/mcp-server:latest serve

2. Configure Your Client
------------------------

.. tab-set::

   .. tab-item:: Cursor IDE (Local)

      **macOS/Linux:** ``~/.cursor/mcp.json``

      **Windows:** ``%APPDATA%\Cursor\mcp.json``

      .. code-block:: json

         {
           "mcpServers": {
             "kubeflow": {
               "command": "kubeflow-mcp",
               "args": ["serve"]
             }
           }
         }

   .. tab-item:: Cursor IDE (Container)

      Use the GHCR container image with kubeconfig volume mount:

      .. code-block:: json

         {
           "mcpServers": {
             "kubeflow": {
               "command": "docker",
               "args": [
                 "run", "-i", "--rm",
                 "-v", "${HOME}/.kube:/root/.kube:ro",
                 "ghcr.io/kubeflow/mcp-server:latest",
                 "serve"
               ]
             }
           }
         }

      .. note::

         Replace ``${HOME}`` with your actual home path on Windows (e.g., ``C:/Users/you/.kube``).

   .. tab-item:: Claude Desktop (macOS)

      **Config:** ``~/Library/Application Support/Claude/claude_desktop_config.json``

      **Local install:**

      .. code-block:: json

         {
           "mcpServers": {
             "kubeflow": {
               "command": "kubeflow-mcp",
               "args": ["serve"]
             }
           }
         }

      **Container:**

      .. code-block:: json

         {
           "mcpServers": {
             "kubeflow": {
               "command": "docker",
               "args": [
                 "run", "-i", "--rm",
                 "-v", "/Users/YOUR_USERNAME/.kube:/root/.kube:ro",
                 "ghcr.io/kubeflow/mcp-server:latest",
                 "serve"
               ]
             }
           }
         }

   .. tab-item:: Claude Desktop (Linux)

      **Config:** ``~/.config/Claude/claude_desktop_config.json``

      **Local install:**

      .. code-block:: json

         {
           "mcpServers": {
             "kubeflow": {
               "command": "kubeflow-mcp",
               "args": ["serve"]
             }
           }
         }

      **Container:**

      .. code-block:: json

         {
           "mcpServers": {
             "kubeflow": {
               "command": "docker",
               "args": [
                 "run", "-i", "--rm",
                 "-v", "/home/YOUR_USERNAME/.kube:/root/.kube:ro",
                 "ghcr.io/kubeflow/mcp-server:latest",
                 "serve"
               ]
             }
           }
         }

   .. tab-item:: Claude Desktop (Windows)

      **Config:** ``%APPDATA%\Claude\claude_desktop_config.json``

      **Local install:**

      .. code-block:: json

         {
           "mcpServers": {
             "kubeflow": {
               "command": "kubeflow-mcp",
               "args": ["serve"]
             }
           }
         }

      **Container (Docker Desktop):**

      .. code-block:: json

         {
           "mcpServers": {
             "kubeflow": {
               "command": "docker",
               "args": [
                 "run", "-i", "--rm",
                 "-v", "C:/Users/YOUR_USERNAME/.kube:/root/.kube:ro",
                 "ghcr.io/kubeflow/mcp-server:latest",
                 "serve"
               ]
             }
           }
         }

Restart your client after saving.

.. note::

   **Volume Mount:** The ``-v ~/.kube:/root/.kube:ro`` mount gives the container
   read-only access to your kubeconfig. The server uses this to connect to Kubernetes.

   Verify your kubeconfig works:

   .. code-block:: bash

      kubectl get nodes

3. Try It
---------

.. code-block:: text

   "What GPU resources are available in my cluster?"
   "Fine-tune google/gemma-2b on alpaca with batch size 2"
   "Show me the training logs"

The assistant will preview configurations before submitting (requires confirmation).

.. warning::

   Training jobs consume cluster resources. Always review before confirming.

Next: :doc:`configuration` | :doc:`../guide/tools` | :doc:`../guide/agents`
