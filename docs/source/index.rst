Kubeflow MCP Server
===================

**AI-Powered Interface for Kubeflow Training**

The Kubeflow MCP Server provides an AI-powered interface for managing distributed training
jobs on Kubernetes through the Model Context Protocol (MCP). It enables AI assistants like
Claude, Cursor, and custom agents to interact with Kubeflow Training Operator.

----

Quick Start
-----------

.. code-block:: bash

   pip install kubeflow-mcp
   kubeflow-mcp serve

Then configure your MCP client to connect. See :doc:`getting-started/quickstart` for details.

----

Why Kubeflow MCP Server?
------------------------

.. grid:: 2
   :gutter: 3

   .. grid-item-card:: 🤖 AI-Native Interface
      
      Natural language interaction with Kubeflow through the MCP protocol.
      No need to learn kubectl or YAML - just describe what you want.

   .. grid-item-card:: 🛡️ Safe by Default
      
      Confirmation required for destructive operations. Namespace isolation
      and policy-based access control protect your cluster.

   .. grid-item-card:: 📊 Token Efficient
      
      Progressive and semantic tool loading modes reduce context usage
      by up to 92%, enabling use with smaller models.

   .. grid-item-card:: 🔧 Extensible
      
      Custom personas, allow/deny lists, and pluggable backends.
      Integrate with your existing security policies.

----

Guides
------

.. grid:: 2
   :gutter: 3

   .. grid-item-card:: Getting Started
      :link: getting-started/index
      :link-type: doc

      Install the server and connect your first MCP client.

   .. grid-item-card:: Tools Reference
      :link: guide/tools
      :link-type: doc

      Explore the 16 tools for planning, training, and monitoring.

   .. grid-item-card:: MCP Prompts
      :link: guide/prompts
      :link-type: doc

      Use guided workflows for common tasks like fine-tuning.

   .. grid-item-card:: Local Agent
      :link: guide/agents
      :link-type: doc

      Run an Ollama-powered agent in your terminal.

----

Supported Tools
---------------

.. list-table::
   :header-rows: 1
   :widths: 25 15 60

   * - Category
     - Count
     - Tools
   * - **Planning**
     - 2
     - ``get_cluster_resources``, ``estimate_resources``
   * - **Discovery**
     - 5
     - ``list_training_jobs``, ``get_training_job``, ``list_runtimes``, ``get_runtime``, ``get_runtime_packages``
   * - **Training**
     - 3
     - ``fine_tune``, ``run_custom_training``, ``run_container_training``
   * - **Monitoring**
     - 3
     - ``get_training_logs``, ``get_training_events``, ``wait_for_training``
   * - **Lifecycle**
     - 3
     - ``delete_training_job``, ``suspend_training_job``, ``resume_training_job``

----

MCP Clients
-----------

Compatible with any MCP client:

- **Cursor IDE** - AI-powered code editor with built-in MCP support
- **Claude Desktop** - Anthropic's desktop app
- **Custom Agents** - Build your own with LlamaIndex, LangChain, or any MCP SDK

----

Getting Involved
----------------

.. grid:: 3
   :gutter: 3

   .. grid-item-card:: 💬 Community
      :link: https://www.kubeflow.org/docs/about/community/#slack-channels

      Join ``#kubeflow-ml-experience`` on CNCF Slack.

   .. grid-item-card:: 🤝 Contribute
      :link: https://github.com/kubeflow/mcp-server

      Browse issues, submit PRs, and help improve the project.

   .. grid-item-card:: 📚 Resources
      :link: https://github.com/kubeflow/community/tree/master/proposals/936-kubeflow-mcp-server

      Read KEP-936 for the design and roadmap.

----

.. toctree::
   :maxdepth: 2
   :hidden:
   :caption: Getting Started

   getting-started/index
   getting-started/installation
   getting-started/quickstart
   getting-started/configuration

.. toctree::
   :maxdepth: 2
   :hidden:
   :caption: User Guide

   guide/tools
   guide/prompts
   guide/resources
   guide/agents

.. toctree::
   :maxdepth: 2
   :hidden:
   :caption: API Reference

   api/tools
   api/core
   api/agents

.. toctree::
   :maxdepth: 2
   :hidden:
   :caption: Development

   development/contributing
   development/architecture
