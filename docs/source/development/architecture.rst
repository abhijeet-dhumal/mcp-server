Architecture
============

Full docs: `ARCHITECTURE.md <https://github.com/kubeflow/mcp-server/blob/main/ARCHITECTURE.md>`_

.. mermaid::

   flowchart LR
       subgraph Clients
           C1[Cursor/Claude]
           C2[Custom Agents]
       end
       subgraph Server
           S[kubeflow-mcp]
       end
       subgraph K8s
           T[TrainerClient]
           J[TrainJobs]
       end
       Clients <-->|MCP| Server --> T --> J

Components
----------

**Core:** ``server.py`` (FastMCP), ``config.py``, ``policy.py``, ``prompts.py``, ``resources.py``

**Trainer:** ``training.py``, ``monitoring.py``, ``discovery.py``, ``lifecycle.py``

**Agents:** ``ollama.py``, ``dynamic_tools.py``, ``mcp_client.py``

Principles
----------

1. **Safe** - Confirmation required for mutations
2. **Efficient** - Up to 92% token reduction
3. **Consistent** - Same protocol for all clients
4. **Extensible** - Policy-based access control
