MCP Prompts
===========

The server provides workflow prompts that guide users through common tasks.
Prompts are reusable message templates that provide structured guidance.

Overview
--------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Prompt
     - Description
   * - ``fine_tuning_workflow``
     - Step-by-step guide for LLM fine-tuning
   * - ``custom_training_workflow``
     - Guide for custom script/container training
   * - ``troubleshooting_guide``
     - Diagnose and fix common failures
   * - ``resource_planning``
     - Plan resources before training
   * - ``monitoring_workflow``
     - Monitor jobs and debug issues

Using Prompts
-------------

In Cursor/Claude
^^^^^^^^^^^^^^^^

Simply ask for the workflow:

.. code-block:: text

   "Guide me through fine-tuning a model"

The MCP client will automatically use the ``fine_tuning_workflow`` prompt.

.. tip::

   You can also request specific prompts by name:
   "Use the troubleshooting_guide to help me fix my failed job"

Programmatic Access
^^^^^^^^^^^^^^^^^^^

MCP clients can programmatically list and fetch prompts:

.. code-block:: python

   # List available prompts
   prompts = await client.list_prompts()

   # Get a specific prompt
   prompt = await client.get_prompt("fine_tuning_workflow")

Prompt Details
--------------

fine_tuning_workflow
^^^^^^^^^^^^^^^^^^^^

A comprehensive guide for fine-tuning language models.

**Steps covered:**

1. Check cluster resources (GPU availability)
2. Select and validate model
3. Estimate resource requirements
4. Choose dataset
5. Configure training parameters
6. Submit job with preview
7. Monitor progress

**When to use:**

- First time fine-tuning with Kubeflow
- Need step-by-step guidance
- Want to ensure best practices

custom_training_workflow
^^^^^^^^^^^^^^^^^^^^^^^^

Guide for running custom training scripts or containers.

**Steps covered:**

1. Choose training approach (function vs container)
2. Configure workers and resources
3. Set up distributed training
4. Submit and monitor

troubleshooting_guide
^^^^^^^^^^^^^^^^^^^^^

Diagnose and fix common training failures.

**Issues covered:**

- OOMKilled errors (out of memory)
- FailedScheduling (insufficient resources)
- ImagePullBackOff (container issues)
- NCCL timeouts (multi-node networking)
- Training crashes and exceptions

**Example prompt:**

.. code-block:: text

   "My training job failed with OOMKilled, help me debug it"

resource_planning
^^^^^^^^^^^^^^^^^

Plan resources before submitting training jobs.

**Helps with:**

- GPU memory estimation
- Batch size selection
- Multi-node configuration
- Cost optimization

monitoring_workflow
^^^^^^^^^^^^^^^^^^^

Monitor running jobs and debug issues.

**Steps covered:**

1. Check job status
2. Stream logs
3. View Kubernetes events
4. Wait for completion
5. Handle failures

What's Next?
------------

- :doc:`resources` - Access read-only reference data
- :doc:`tools` - Explore all available tools
- :doc:`agents` - Set up the local agent
