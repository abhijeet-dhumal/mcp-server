MCP Prompts
===========

Workflow prompts guide users through common tasks.

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Prompt
     - Description
   * - ``fine_tuning_workflow``
     - Step-by-step LLM fine-tuning guide
   * - ``custom_training_workflow``
     - Custom script/container training
   * - ``troubleshooting_guide``
     - Diagnose and fix failures
   * - ``resource_planning``
     - Plan resources before training
   * - ``monitoring_workflow``
     - Monitor jobs and debug issues

Usage
-----

Ask naturally:

.. code-block:: text

   "Guide me through fine-tuning a model"
   "Help me troubleshoot my failed job"

Programmatic:

.. code-block:: python

   prompts = await client.list_prompts()
   prompt = await client.get_prompt("fine_tuning_workflow")

Next: :doc:`resources` | :doc:`tools` | :doc:`agents`
