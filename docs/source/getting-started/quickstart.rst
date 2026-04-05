Quick Start
===========

This guide walks you through connecting an MCP client and running your first training job.

Prerequisites
-------------

Before you begin, make sure you have:

1. The Kubeflow MCP Server installed (see :doc:`installation`)
2. An MCP client (Cursor IDE, Claude Desktop, or similar)
3. Access to a Kubernetes cluster with Kubeflow Training Operator

.. note::

   New to MCP? The Model Context Protocol lets AI assistants use tools and
   access resources. Learn more at `modelcontextprotocol.io <https://modelcontextprotocol.io>`_.

Step 1: Start the Server
------------------------

Start the MCP server in stdio mode (default):

.. code-block:: bash

   kubeflow-mcp serve

You should see:

.. code-block:: text

   INFO: Starting kubeflow-mcp (clients=trainer, persona=ml-engineer)

Step 2: Connect Your Client
---------------------------

Cursor IDE
^^^^^^^^^^

Add to your Cursor MCP settings (``~/.cursor/mcp.json``):

.. code-block:: json

   {
     "mcpServers": {
       "kubeflow": {
         "command": "kubeflow-mcp",
         "args": ["serve"]
       }
     }
   }

Claude Desktop
^^^^^^^^^^^^^^

Add to ``~/Library/Application Support/Claude/claude_desktop_config.json`` (macOS):

.. code-block:: json

   {
     "mcpServers": {
       "kubeflow": {
         "command": "kubeflow-mcp",
         "args": ["serve"]
       }
     }
   }

.. tip::

   Restart your MCP client after adding the configuration.

Step 3: Verify Connection
-------------------------

Ask your AI assistant:

.. code-block:: text

   "What Kubeflow tools are available?"

You should see a list of 16 tools across planning, discovery, training, monitoring, and lifecycle categories.

Step 4: Check Cluster Resources
-------------------------------

Before training, check what's available:

.. code-block:: text

   "What GPU resources are available in my cluster?"

The assistant will use the ``get_cluster_resources`` tool to show:

- Total GPU count and types
- Available CPU and memory
- Node information

Step 5: Fine-Tune a Model
-------------------------

Now let's fine-tune a model. Ask:

.. code-block:: text

   "Fine-tune google/gemma-2b on the alpaca dataset with batch size 2"

The assistant will:

1. **Preview** the job configuration (``confirmed=False``)
2. Ask for your confirmation
3. **Submit** the job (``confirmed=True``)
4. Return the job name

.. warning::

   Training jobs consume cluster resources. Always review the preview before confirming.

Step 6: Monitor Progress
------------------------

Track your job:

.. code-block:: text

   "Show me the training logs for my job"

Or check events:

.. code-block:: text

   "What's the status of my training job?"

Common Patterns
---------------

**Estimate resources before training:**

.. code-block:: text

   "How much GPU memory do I need to fine-tune Llama-3.2-3B?"

**Use guided workflows:**

.. code-block:: text

   "Guide me through fine-tuning a model"

This uses the ``fine_tuning_workflow`` prompt for step-by-step guidance.

**Troubleshoot failures:**

.. code-block:: text

   "My training job failed with OOMKilled, help me fix it"

What's Next?
------------

- :doc:`configuration` - Customize server behavior and policies
- :doc:`../guide/tools` - Explore all 16 available tools
- :doc:`../guide/prompts` - Learn about guided workflow prompts
- :doc:`../guide/agents` - Set up the local Ollama agent
