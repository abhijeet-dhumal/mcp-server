"""Persona definitions for tool access control."""

PERSONAS: dict[str, dict] = {
    "readonly": {
        "tools": [
            "get_cluster_resources",
            "list_training_jobs",
            "get_training_job",
            "get_training_logs",
            "get_training_events",
            "list_runtimes",
            "get_runtime",
            "health_check",
            "get_server_logs",
        ]
    },
    "data-scientist": {
        "inherit": "readonly",
        "tools": [
            "estimate_resources",
            "fine_tune",
            "run_custom_training",
            "wait_for_training",
            "delete_training_job",
        ],
    },
    "ml-engineer": {
        "inherit": "data-scientist",
        "tools": [
            "run_container_training",
            "get_runtime_packages",
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
