Kubeflow MCP Server
===================

**AI-Powered Interface for Kubeflow Training**

Enable AI assistants to manage distributed training jobs on Kubernetes through the
Model Context Protocol (MCP). Works with Claude, Cursor, and custom agents.

.. code-block:: bash

   pip install kubeflow-mcp
   kubeflow-mcp serve

----

.. grid:: 2
   :gutter: 3

   .. grid-item-card:: 🤖 AI-Native
      
      Natural language interaction - no kubectl or YAML needed.

   .. grid-item-card:: 🛡️ Safe by Default
      
      Confirmation required for mutations, namespace isolation.

   .. grid-item-card:: 📊 Token Efficient
      
      Up to 92% context reduction with progressive/semantic modes.

   .. grid-item-card:: 🔧 Extensible
      
      Custom personas and policy-based access control.

----

.. grid:: 2
   :gutter: 3

   .. grid-item-card:: Getting Started
      :link: getting-started/quickstart
      :link-type: doc

      Install and connect your first MCP client.

   .. grid-item-card:: Tools (16)
      :link: guide/tools
      :link-type: doc

      Planning, training, monitoring, lifecycle tools.

   .. grid-item-card:: Prompts
      :link: guide/prompts
      :link-type: doc

      Guided workflows for fine-tuning and troubleshooting.

   .. grid-item-card:: Local Agent
      :link: guide/agents
      :link-type: doc

      Terminal-based Ollama agent.

----

**Clients:** Cursor IDE, Claude Desktop, custom LlamaIndex/LangChain agents

**Community:** `#kubeflow-ml-experience <https://www.kubeflow.org/docs/about/community/#slack-channels>`_ on CNCF Slack

----

.. toctree::
   :maxdepth: 2
   :hidden:
   :caption: Getting Started

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
