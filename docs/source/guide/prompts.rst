MCP Prompts
===========

Workflow prompts guide users through common tasks. 

They do not run jobs by themselves. Instead, they generate structured guidance
that helps users and agents call the right tools in the right order.

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

Prompt Inputs
-------------

Some prompts accept optional arguments to tailor their output.

.. list-table::
   :header-rows: 1
   :widths: 30 25 45

   * - Prompt
     - Optional arguments
     - Notes
   * - ``fine_tuning_workflow``
     - ``model``, ``dataset``
     - If omitted, prompt uses generic placeholders.
   * - ``custom_training_workflow``
     - ``training_type``
     - Use ``script`` (default) or ``container``.
   * - ``troubleshooting_guide``
     - ``error_type``
     - Examples: ``oom``, ``pending``, ``runtime``, ``permission``.
   * - ``resource_planning``
     - ``model_size``
     - Can be used to adjust planning guidance.
   * - ``monitoring_workflow``
     - ``job_name``
     - Focuses monitoring steps for a specific job.

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

Programmatic with arguments:

.. code-block:: python

   prompt = await client.get_prompt(
     "fine_tuning_workflow",
     arguments={
       "model": "meta-llama/Llama-3.2-3B",
       "dataset": "tatsu-lab/alpaca",
     },
   )

Best Practices
--------------

- Start with prompt guidance, then execute tools step-by-step.
- Treat submission calls as two-stage: preview first, then confirm.
- Re-run planning prompts when model, batch size, or runtime changes.
- Pair troubleshooting prompts with fresh events/logs from the target namespace.
- Keep persona/policy constraints in mind; available tools may differ by role.

Next: :doc:`resources` | :doc:`tools` | :doc:`agents`
