MCP Resources
=============

The server exposes read-only resources for reference data.
Resources are cacheable and don't consume tool call quota.

Overview
--------

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Resource URI
     - Description
   * - ``trainer://models/supported``
     - Tested model configurations with GPU requirements
   * - ``trainer://runtimes/info``
     - Training runtime documentation
   * - ``trainer://guides/quickstart``
     - Quick start guide for new users
   * - ``trainer://guides/troubleshooting``
     - Troubleshooting quick reference

.. note::

   Resources are read-only data that clients can fetch and cache.
   Unlike tools, they don't perform actions or consume API quota.

Accessing Resources
-------------------

MCP Client
^^^^^^^^^^

.. code-block:: python

   # List all available resources
   resources = await client.list_resources()

   # Fetch a specific resource
   content = await client.read_resource("trainer://models/supported")

In Conversation
^^^^^^^^^^^^^^^

Ask your AI assistant:

.. code-block:: text

   "Show me the supported models for fine-tuning"

The assistant will fetch the ``trainer://models/supported`` resource.

Resource Details
----------------

trainer://models/supported
^^^^^^^^^^^^^^^^^^^^^^^^^^

Lists tested model configurations with resource requirements.

**Contents:**

- Model names and parameter counts
- GPU memory requirements
- Recommended batch sizes
- Compatible datasets

**Example data:**

.. list-table::
   :header-rows: 1
   :widths: 30 15 20 35

   * - Model
     - Params
     - GPU Memory
     - Batch Size
   * - google/gemma-2b
     - 2B
     - 8GB
     - 2-4
   * - meta-llama/Llama-3.2-3B
     - 3B
     - 16GB
     - 2-4
   * - mistralai/Mistral-7B-v0.1
     - 7B
     - 24GB
     - 1-2

trainer://runtimes/info
^^^^^^^^^^^^^^^^^^^^^^^

Documents available training runtimes.

**Contents:**

- Runtime names and descriptions
- Supported frameworks
- Configuration options
- Customization examples

trainer://guides/quickstart
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Quick start guide for new users.

**Contents:**

1. Cluster resource check
2. Resource estimation
3. Fine-tuning submission
4. Progress monitoring

trainer://guides/troubleshooting
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Quick reference for common issues.

**Contents:**

- Diagnostic commands
- Status meanings
- Common errors and fixes
- Recovery commands

What's Next?
------------

- :doc:`tools` - Explore available tools
- :doc:`prompts` - Use guided workflow prompts
- :doc:`agents` - Try the local agent
