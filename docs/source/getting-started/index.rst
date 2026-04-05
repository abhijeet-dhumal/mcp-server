Getting Started
===============

Get up and running with the Kubeflow MCP Server in minutes.

.. grid:: 2
   :gutter: 3

   .. grid-item-card:: Installation
      :link: installation
      :link-type: doc

      Install the server and dependencies.

   .. grid-item-card:: Quick Start
      :link: quickstart
      :link-type: doc

      Connect your first MCP client and run a training job.

   .. grid-item-card:: Configuration
      :link: configuration
      :link-type: doc

      Customize server behavior with YAML and environment variables.

Prerequisites
-------------

Before you begin, ensure you have:

1. **Python 3.10+** installed
2. **kubectl** configured with cluster access
3. **Kubeflow Training Operator** installed on your cluster

.. note::

   Don't have a cluster? You can still explore the tools and prompts locally.
   The server will validate inputs but won't submit jobs without cluster access.

.. toctree::
   :hidden:

   installation
   quickstart
   configuration
