"""Persona definitions for tool access control.

Personas define which tools are available to different user roles:
- readonly: View-only access for monitoring
- data-scientist: Training job submission
- ml-engineer: Full training management
- platform-admin: Unrestricted access
"""

PERSONAS: dict[str, dict] = {
    "readonly": {
        "tools": [
            # planning
            "get_cluster_resources",
            # discovery
            "list_training_jobs",
            "get_training_job",
            "list_runtimes",
            "get_runtime",
            # monitoring
            "get_training_logs",
            "get_training_events",
            # health
            "health_check",
            "get_server_logs",
        ]
    },
    "data-scientist": {
        "inherit": "readonly",
        "tools": [
            # planning
            "estimate_resources",
            # training
            "fine_tune",
            "run_custom_training",
            # monitoring
            "wait_for_training",
            # lifecycle
            "delete_training_job",
        ],
    },
    "ml-engineer": {
        "inherit": "data-scientist",
        "tools": [
            # training
            "run_container_training",
            # discovery
            "get_runtime_packages",
            # lifecycle
            "suspend_training_job",
            "resume_training_job",
        ],
    },
    "platform-admin": {"tools": "*"},
}


def get_allowed_tools(persona: str) -> set[str] | None:
    """Returns tool names allowed for persona. None means all."""
    if persona not in PERSONAS:
        raise ValueError(f"Unknown persona: {persona}")

    config = PERSONAS[persona]
    if config.get("tools") == "*":
        return None

    tools = set(config.get("tools", []))
    if "inherit" in config:
        parent = get_allowed_tools(config["inherit"])
        if parent:
            tools.update(parent)
    return tools
