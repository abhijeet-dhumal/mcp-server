# Contributing to Kubeflow MCP Server

Thank you for your interest in contributing! This guide will help you get started.

## Development Setup

```bash
# Clone the repository
git clone https://github.com/kubeflow/mcp-server.git
cd mcp-server

# Install all dependencies (requires uv)
make dev

# Verify setup
make check
```

## Project Structure

```
src/kubeflow_mcp/
├── core/           # Server infrastructure
│   ├── server.py   # MCP server factory
│   ├── policy.py   # Persona-based access control
│   └── health.py   # Health check tools
├── trainer/        # Kubeflow Training tools
│   ├── api/        # Tool implementations
│   │   ├── planning.py    # Resource estimation
│   │   ├── training.py    # Job submission
│   │   ├── discovery.py   # Job/runtime listing
│   │   ├── monitoring.py  # Logs and events
│   │   └── lifecycle.py   # Suspend/resume/delete
│   └── skills/     # AI context documents
├── agents/         # Local agent implementations
│   ├── ollama.py   # Ollama-based agent
│   └── dynamic_tools.py  # Progressive/semantic modes
└── cli.py          # Command-line interface
```

## Adding a New Tool

1. **Choose the right module** based on tool category:
   - `planning.py` - Resource checks, estimations
   - `training.py` - Job submission
   - `discovery.py` - Listing resources
   - `monitoring.py` - Logs, events, status
   - `lifecycle.py` - Suspend, resume, delete

2. **Implement the tool function**:

```python
def my_new_tool(param1: str, param2: int = 10) -> dict[str, Any]:
    """Short description for AI context.

    Args:
        param1: Description of param1
        param2: Description with default

    Returns:
        Dict with 'success' and result or 'error'
    """
    try:
        # Implementation using Kubeflow SDK
        client = get_trainer_client()
        result = client.some_method(param1, param2)
        return {"success": True, "data": result}
    except Exception as e:
        return ToolError(
            error=str(e),
            error_code="SDK_ERROR",
        ).model_dump()
```

3. **Register the tool** in `trainer/__init__.py`:

```python
from kubeflow_mcp.trainer.api.your_module import my_new_tool

TOOLS = [
    # ... existing tools
    my_new_tool,
]

TOOL_CATEGORIES = {
    "your_category": [my_new_tool],
}
```

4. **Add tool annotations** in `core/server.py`:

```python
TOOL_ANNOTATIONS = {
    "my_new_tool": {
        "title": "My New Tool",
        "readOnlyHint": True,  # Does it only read?
        "destructiveHint": False,  # Can it delete things?
        "idempotentHint": True,  # Safe to call repeatedly?
        "openWorldHint": True,  # Interacts with external systems?
    },
}
```

5. **Add tests** in `tests/unit/trainer/`:

```python
class TestMyNewTool:
    def test_success(self, mock_client):
        mock_client.some_method.return_value = expected
        result = my_new_tool("value")
        assert result["success"] is True
        
    def test_error_handling(self, mock_client):
        mock_client.some_method.side_effect = Exception("Failed")
        result = my_new_tool("value")
        assert result["success"] is False
```

## Code Quality

Run these before submitting:

```bash
make pre-commit  # Runs format, lint, typecheck, tests
```

Individual commands:

```bash
make lint        # Ruff linter
make format      # Auto-format code
make typecheck   # Mypy type checking
make test-unit   # Unit tests
```

## Testing

```bash
# All tests
make test

# Unit tests only
make test-unit

# With coverage
make test-cov

# Benchmarks
make benchmark
```

### Writing Tests

- Use `@pytest.fixture` for common setup
- Mock external dependencies (SDK, K8s client)
- Test both success and error paths
- Follow existing patterns in `tests/unit/`

## Pull Request Process

1. **Fork** the repository
2. **Create a branch**: `git checkout -b feature/my-feature`
3. **Make changes** following the guidelines above
4. **Run checks**: `make pre-commit`
5. **Sign off** your commits (see DCO below)
6. **Push** and create a Pull Request

### Developer Certificate of Origin (DCO)

All contributions must be signed off per the [DCO](https://developercertificate.org/):

```bash
# Sign off your commit
git commit -s -m "feat: add new feature"

# Or add sign-off to existing commit
git commit --amend -s
```

This adds a `Signed-off-by: Your Name <your@email.com>` line to your commit message.

### Apache 2.0 License Headers

New source files must include the Apache 2.0 license header:

```python
# Copyright 2024 The Kubeflow Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
```

### Commit Message Format

Use [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `refactor:` Code refactoring
- `test:` Adding tests
- `chore:` Maintenance tasks

Example with sign-off:
```
feat: add support for distributed training metrics

- Added get_training_metrics() tool
- Integrated with Kubeflow SDK metrics API
- Added unit tests

Signed-off-by: Jane Doe <jane@example.com>
```

### Prow Commands

This repository uses [Prow](https://docs.prow.k8s.io/) for CI/CD automation. Reviewers and approvers can use these commands in PR comments:

| Command | Who Can Use | Description |
|---------|-------------|-------------|
| `/lgtm` | Reviewers (in OWNERS) | Add "lgtm" label after code review |
| `/approve` | Approvers (in OWNERS) | Add "approved" label, enables merge |
| `/hold` | Anyone | Prevent PR from merging |
| `/hold cancel` | Anyone | Remove hold |
| `/retest` | Anyone | Re-run failed tests |
| `/assign @user` | Anyone | Assign PR to a user |
| `/cc @user` | Anyone | Request review from a user |

PRs require both `lgtm` and `approved` labels to merge. See [OWNERS](OWNERS) for current reviewers and approvers.

## Adding a New Client Module

To add support for new Kubeflow components (e.g., Katib, Model Registry):

1. Create module directory: `src/kubeflow_mcp/your_client/`
2. Implement tools in `api/` subdirectory
3. Export `TOOLS` list in `__init__.py`
4. Register in `core/server.py`:

```python
CLIENT_MODULES = {
    "trainer": "kubeflow_mcp.trainer",
    "your_client": "kubeflow_mcp.your_client",  # Add here
}
```

5. Add optional dependency in `pyproject.toml`:

```toml
[project.optional-dependencies]
your_client = ["kubeflow-your-client>=1.0"]
```

## Good First Issues

Looking for where to start? Check out issues labeled [`good first issue`](https://github.com/kubeflow/mcp-server/labels/good%20first%20issue):

- Add new monitoring metrics tool
- Improve error messages
- Add more unit tests
- Documentation improvements
- Example scripts

## Additional Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) - System design and module structure
- [DEVELOPMENT.md](docs/DEVELOPMENT.md) - Detailed development guide
- [ROADMAP.md](ROADMAP.md) - Planned features
- [SECURITY.md](SECURITY.md) - Security policy and vulnerability reporting

## Questions?

- Open an issue for bugs or feature requests
- Join [#kubeflow-ml-experience](https://www.kubeflow.org/docs/about/community/#slack-channels) on CNCF Slack for discussions
- Check existing issues before creating new ones

## License

By contributing, you agree that your contributions will be licensed under the Apache 2.0 License.
