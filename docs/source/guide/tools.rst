Tools Reference
===============

16 tools organized by workflow phase.

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Phase
     - Tools
   * - **Planning**
     - ``get_cluster_resources``, ``estimate_resources``
   * - **Discovery**
     - ``list_training_jobs``, ``get_training_job``, ``list_runtimes``, ``get_runtime``, ``get_runtime_packages``
   * - **Training**
     - ``fine_tune``, ``run_custom_training``, ``run_container_training``
   * - **Monitoring**
     - ``get_training_logs``, ``get_training_events``, ``wait_for_training``
   * - **Lifecycle**
     - ``delete_training_job``, ``suspend_training_job``, ``resume_training_job``

Planning
--------

``get_cluster_resources``
   Returns GPU count/types, CPU, memory, and node info.

``estimate_resources``
   Estimates GPU memory and batch size for a model.

Discovery
---------

``list_training_jobs``
   List jobs in namespace, filter by runtime/status.

``get_training_job``
   Get details of a specific job.

``list_runtimes`` / ``get_runtime`` / ``get_runtime_packages``
   Explore available ClusterTrainingRuntimes.

Training
--------

``fine_tune``
   Fine-tune LLMs with LoRA/QLoRA.

   .. list-table::
      :widths: 25 75

      * - ``model``
        - HuggingFace model (e.g., ``hf://google/gemma-2b``)
      * - ``dataset``
        - Training dataset (e.g., ``hf://tatsu-lab/alpaca``)
      * - ``batch_size``
        - Training batch size (default: 4)
      * - ``epochs``
        - Training epochs (default: 1)
      * - ``confirmed``
        - ``False`` = preview, ``True`` = submit

``run_custom_training``
   Run custom Python training functions.

``run_container_training``
   Run training with custom container images.

Monitoring
----------

``get_training_logs``
   Stream pod logs for a job.

``get_training_events``
   Get Kubernetes events (scheduling, errors).

``wait_for_training``
   Block until job completes or fails.

Lifecycle
---------

``delete_training_job``
   Delete a training job (requires confirmation).

``suspend_training_job`` / ``resume_training_job``
   Pause and resume running jobs.

Confirmation
------------

These tools require ``confirmed=True``:

- ``fine_tune``, ``run_custom_training``, ``run_container_training``
- ``delete_training_job``

Next: :doc:`prompts` | :doc:`resources` | :doc:`agents`
