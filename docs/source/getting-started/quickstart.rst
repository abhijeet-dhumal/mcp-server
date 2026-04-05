Quick Start
===========

Connect an MCP client and run your first training job.

1. Start the Server
-------------------

.. code-block:: bash

   kubeflow-mcp serve

2. Configure Your Client
------------------------

**Cursor IDE** (``~/.cursor/mcp.json``):

.. code-block:: json

   {
     "mcpServers": {
       "kubeflow": {
         "command": "kubeflow-mcp",
         "args": ["serve"]
       }
     }
   }

**Claude Desktop** (``~/Library/Application Support/Claude/claude_desktop_config.json``):

.. code-block:: json

   {
     "mcpServers": {
       "kubeflow": {
         "command": "kubeflow-mcp",
         "args": ["serve"]
       }
     }
   }

Restart your client after saving.

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
