Tools Reference
===============

The Kubeflow MCP Server exposes 16 tools organized by workflow phase.

Overview
--------

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Phase
     - Description
   * - **Planning**
     - Check cluster resources and estimate requirements before training
   * - **Discovery**
     - List and inspect jobs, runtimes, and configurations
   * - **Training**
     - Submit fine-tuning, custom, and container training jobs
   * - **Monitoring**
     - Get logs, events, and wait for job completion
   * - **Lifecycle**
     - Delete, suspend, and resume training jobs

Planning Tools
--------------

get_cluster_resources
^^^^^^^^^^^^^^^^^^^^^

Check available resources in the cluster before submitting jobs.

**Returns:**

- Total GPU count and types
- Available CPU and memory
- Node information

**Example prompt:**

.. code-block:: text

   "What resources are available in my cluster?"

estimate_resources
^^^^^^^^^^^^^^^^^^

Estimate GPU memory and compute requirements for a model.

**Parameters:**

- ``model``: Model identifier (e.g., ``google/gemma-2b``)

**Returns:**

- Estimated GPU memory
- Recommended batch size
- Suggested configuration

**Example prompt:**

.. code-block:: text

   "How much GPU memory do I need to fine-tune Llama-3.2-3B?"

Discovery Tools
---------------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Tool
     - Description
   * - ``list_training_jobs``
     - List all training jobs in namespace
   * - ``get_training_job``
     - Get details of a specific job
   * - ``list_runtimes``
     - List available ClusterTrainingRuntimes
   * - ``get_runtime``
     - Get runtime configuration details
   * - ``get_runtime_packages``
     - List packages installed in a runtime

Training Tools
--------------

fine_tune
^^^^^^^^^

Fine-tune a language model using LoRA or QLoRA.

**Parameters:**

.. list-table::
   :widths: 20 15 65

   * - Parameter
     - Default
     - Description
   * - ``model``
     - (required)
     - Model to fine-tune (e.g., ``hf://google/gemma-2b``)
   * - ``dataset``
     - (required)
     - Training dataset (e.g., ``hf://tatsu-lab/alpaca``)
   * - ``batch_size``
     - 4
     - Training batch size
   * - ``epochs``
     - 1
     - Number of training epochs
   * - ``lora_rank``
     - 8
     - LoRA rank for parameter-efficient tuning
   * - ``confirmed``
     - False
     - Set True to actually submit (False = preview)

**Example prompt:**

.. code-block:: text

   "Fine-tune gemma-2b on alpaca with batch size 2 for 3 epochs"

.. note::

   The ``hf://`` prefix indicates a HuggingFace model or dataset.

run_custom_training
^^^^^^^^^^^^^^^^^^^

Run a custom Python training function on the cluster.

**Example prompt:**

.. code-block:: text

   "Run my custom training script with 2 workers"

run_container_training
^^^^^^^^^^^^^^^^^^^^^^

Run training with a custom container image.

**Example prompt:**

.. code-block:: text

   "Run training with my container image my-registry/my-trainer:latest"

Monitoring Tools
----------------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Tool
     - Description
   * - ``get_training_logs``
     - Get pod logs for a training job
   * - ``get_training_events``
     - Get Kubernetes events for a job
   * - ``wait_for_training``
     - Block until job completes or fails

Lifecycle Tools
---------------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Tool
     - Description
   * - ``delete_training_job``
     - Delete a training job
   * - ``suspend_training_job``
     - Suspend a running job
   * - ``resume_training_job``
     - Resume a suspended job

Confirmation Required
---------------------

The following tools require explicit confirmation (``confirmed=True``):

- ``fine_tune``
- ``run_custom_training``
- ``run_container_training``
- ``delete_training_job``

.. warning::

   This prevents accidental resource creation or deletion. Always review
   the preview output before confirming.

What's Next?
------------

- :doc:`prompts` - Use guided workflow prompts
- :doc:`resources` - Access read-only reference data
- :doc:`agents` - Try the local Ollama agent
