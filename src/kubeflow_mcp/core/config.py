"""Configuration schema for kubeflow-mcp."""

import os

from pydantic import BaseModel, Field


class ServerConfig(BaseModel):
    """Server configuration."""

    clients: list[str] = Field(default=["trainer"])
    persona: str = Field(default="ml-engineer")
    namespaces: list[str] | None = None
    transport: str = Field(default="stdio")


class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: str = Field(default="INFO")
    format: str | None = Field(default=None)


class Config(BaseModel):
    """Root configuration."""

    server: ServerConfig = Field(default_factory=ServerConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)


def load_config() -> Config:
    """Load configuration from environment variables."""
    return Config(
        server=ServerConfig(
            clients=os.getenv("KUBEFLOW_MCP_CLIENTS", "trainer").split(","),
            persona=os.getenv("KUBEFLOW_MCP_PERSONA", "ml-engineer"),
            transport=os.getenv("MCP_TRANSPORT", "stdio"),
        ),
        logging=LoggingConfig(
            level=os.getenv("LOG_LEVEL", "INFO"),
            format=os.getenv("LOG_FORMAT"),
        ),
    )
