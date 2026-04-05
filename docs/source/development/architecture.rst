Architecture
============

For the full architecture documentation, see
`ARCHITECTURE.md <https://github.com/kubeflow/mcp-server/blob/main/ARCHITECTURE.md>`_
in the repository.

Overview
--------

.. mermaid::

   flowchart TB
       subgraph Clients["MCP Clients"]
           C1[Cursor IDE]
           C2[Claude Desktop]
           C3[Custom Agents]
       end

       subgraph Server["MCP Server (FastMCP)"]
           S[kubeflow-mcp]
       end

       subgraph SDK["Kubeflow SDK"]
           T[TrainerClient]
       end

       subgraph K8s["Kubernetes"]
           J[TrainJobs]
       end

       Clients <-->|MCP Protocol| Server
       Server --> SDK
       SDK --> K8s

Components
----------

Core
^^^^

- ``server.py`` - FastMCP server setup, tool registration
- ``config.py`` - Configuration loading from YAML/env
- ``policy.py`` - Persona-based access control
- ``prompts.py`` - MCP prompt definitions
- ``resources.py`` - MCP resource definitions

Trainer
^^^^^^^

- ``training.py`` - Fine-tune, custom training tools
- ``monitoring.py`` - Logs, events, wait tools
- ``discovery.py`` - List jobs, runtimes tools
- ``lifecycle.py`` - Delete, suspend, resume tools
- ``resources.py`` - Cluster resource tools

Agents
^^^^^^

- ``ollama.py`` - Local Ollama agent
- ``dynamic_tools.py`` - Token-efficient toolsets
- ``mcp_client.py`` - In-process MCP client

Design Principles
-----------------

1. **Safe by Default** - Confirmation required for mutations
2. **Token Efficient** - Progressive/semantic modes reduce context
3. **Protocol Consistent** - Same MCP protocol for all clients
4. **Extensible** - Policy-based access control
