Local Agent
===========

The Kubeflow MCP Server includes a local agent powered by Ollama for
terminal-based interaction. No external MCP client needed.

Prerequisites
-------------

1. **Install Ollama:** Download from https://ollama.ai

2. **Pull a model:**

   .. code-block:: bash

      ollama pull qwen3:8b

3. **Install agent dependencies:**

   .. code-block:: bash

      pip install kubeflow-mcp[agents]

.. note::

   The local agent requires additional dependencies for LlamaIndex and Rich.
   These are installed with the ``agents`` extra.

Running the Agent
-----------------

.. code-block:: bash

   kubeflow-mcp agent

Or with Make:

.. code-block:: bash

   make agent

Options
^^^^^^^

.. list-table::
   :header-rows: 1
   :widths: 20 20 60

   * - Option
     - Default
     - Description
   * - ``--backend, -b``
     - ``ollama``
     - LLM backend
   * - ``--model, -m``
     - ``qwen3:8b``
     - Model name
   * - ``--mode``
     - ``full``
     - Tool loading mode (full, progressive, semantic)
   * - ``--thinking``
     - off
     - Enable thinking output for supported models

Tool Loading Modes
------------------

The agent supports three modes for different context budgets:

Full Mode (Default)
^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   kubeflow-mcp agent --mode full

- All 16 tools loaded via MCP protocol
- ~900 tokens initial context
- Best accuracy for capable models

Progressive Mode
^^^^^^^^^^^^^^^^

.. code-block:: bash

   kubeflow-mcp agent --mode progressive

- 3 meta-tools for hierarchical discovery
- ~85 tokens initial context (~91% reduction)
- Tools loaded on-demand by category

Semantic Mode
^^^^^^^^^^^^^

.. code-block:: bash

   kubeflow-mcp agent --mode semantic

- 2 meta-tools with embedding search
- ~69 tokens initial context (~92% reduction)
- Best for constrained contexts

Mode Comparison
^^^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1
   :widths: 20 15 15 50

   * - Mode
     - Tools
     - Tokens
     - Use Case
   * - Full
     - 16
     - ~900
     - Default, capable models
   * - Progressive
     - 3
     - ~85
     - Category-based discovery
   * - Semantic
     - 2
     - ~69
     - Natural language search

.. tip::

   Start with ``full`` mode. Only switch to ``progressive`` or ``semantic``
   if you're using a smaller model or hitting context limits.

Example Session
---------------

.. code-block:: text

   $ kubeflow-mcp agent

   ╭─────────────────────────────────────────────╮
   │  🚀 Kubeflow AI Agent                       │
   │  Type 'quit' to exit, 'help' for commands  │
   ╰─────────────────────────────────────────────╯

   You: What GPUs are available?

   Agent: Let me check the cluster resources...

   [Calling get_cluster_resources]

   Your cluster has:
   - 4 NVIDIA A100 GPUs (80GB each)
   - 320GB total GPU memory
   - 2 GPU nodes

   You: Fine-tune gemma-2b on alpaca

   Agent: I'll set up fine-tuning for you...

Interactive Commands
--------------------

.. list-table::
   :widths: 20 80

   * - ``/help``
     - Show available commands
   * - ``/tools``
     - List available tools
   * - ``/mode <name>``
     - Switch tool mode (full/progressive/semantic)
   * - ``/think``
     - Toggle thinking output
   * - ``quit`` or ``exit``
     - Exit the agent

Architecture
------------

The local agent uses the same MCP protocol as external clients:

.. mermaid::

   flowchart LR
       A[Local Agent<br/>Ollama] <-->|stdio| B[MCP Server<br/>kubeflow-mcp]

This ensures consistent behavior across all clients.

What's Next?
------------

- :doc:`tools` - Explore available tools
- :doc:`prompts` - Use guided workflow prompts
- :doc:`../getting-started/configuration` - Configure server behavior
