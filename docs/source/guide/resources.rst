MCP Resources
=============

Read-only reference data (cacheable, no tool quota).

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - URI
     - Content
   * - ``trainer://models/supported``
     - Model configs with GPU requirements
   * - ``trainer://runtimes/info``
     - Runtime documentation
   * - ``trainer://guides/quickstart``
     - Quick start guide
   * - ``trainer://guides/troubleshooting``
     - Troubleshooting reference

Usage
-----

.. code-block:: python

   resources = await client.list_resources()
   content = await client.read_resource("trainer://models/supported")

Next: :doc:`tools` | :doc:`prompts` | :doc:`agents`
