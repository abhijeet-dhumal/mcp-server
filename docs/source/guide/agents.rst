Local Agent
===========

Terminal-based agent powered by Ollama.

Setup
-----

.. code-block:: bash

   pip install kubeflow-mcp[agents]
   ollama pull qwen3:8b
   kubeflow-mcp agent

Options
-------

.. list-table::
   :widths: 25 25 50

   * - Option
     - Default
     - Description
   * - ``--model``
     - ``qwen3:8b``
     - Ollama model
   * - ``--mode``
     - ``full``
     - Tool loading mode
   * - ``--thinking``
     - off
     - Show model reasoning

Tool Modes
----------

.. list-table::
   :widths: 20 20 60

   * - Mode
     - Tokens
     - Description
   * - ``full``
     - ~900
     - All 16 tools via MCP
   * - ``progressive``
     - ~85
     - 3 meta-tools, hierarchical discovery
   * - ``semantic``
     - ~69
     - 2 meta-tools, embedding search

Commands
--------

``/tools`` - List tools | ``/mode <name>`` - Switch mode | ``/think`` - Toggle thinking

Architecture
------------

.. mermaid::

   flowchart LR
       A[Ollama Agent] <-->|stdio| B[MCP Server]

Same protocol as Cursor/Claude - consistent behavior.

Next: :doc:`tools` | :doc:`prompts` | :doc:`../getting-started/configuration`
