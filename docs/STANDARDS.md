# WoodYou - Engineering Standards

## Version 1.0 - Last updated: 2025-04-25

> **Read this once, keep it open while you code.**
> Any pull-request that violates a MUST/SHALL rule will fail CI.

## Table of Contents

- [WoodYou - Engineering Standards](#woodyou---engineering-standards)
  - [Version 1.0 - Last updated: 2025-04-25](#version-10---last-updated-2025-04-25)
  - [Table of Contents](#table-of-contents)
  - [1. Directory conventions](#1-directory-conventions)
  - [2. Coding style](#2-coding-style)
    - [2.1 Python](#21-python)
      - [2.1.1 Naming Conventions](#211-naming-conventions)
      - [2.1.2 Code Organization](#212-code-organization)
      - [2.1.3 Error Handling](#213-error-handling)
      - [2.1.4 Type Annotations](#214-type-annotations)
      - [2.1.5 Comments](#215-comments)
      - [2.1.6 Testing](#216-testing)
    - [2.2 Bash](#22-bash)
    - [2.3 Dockerfiles](#23-dockerfiles)
    - [2.4 SQL Style](#24-sql-style)
    - [2.5 API Design](#25-api-design)
    - [2.6 Pre-commit configuration](#26-pre-commit-configuration)
  - [3. Dependency management](#3-dependency-management)
  - [4. Security \& secrets](#4-security--secrets)
  - [5. Testing](#5-testing)
  - [6. Commit \& PR process](#6-commit--pr-process)
    - [6.1 Commit messages](#61-commit-messages)
    - [6.2 Branches](#62-branches)
    - [6.3 Pull-requests](#63-pull-requests)
  - [7. Documentation](#7-documentation)
  - [8. DevContainer \& local setup](#8-devcontainer--local-setup)
  - [9. CI/CD pipeline](#9-cicd-pipeline)
  - [10. Issue \& Project workflow](#10-issue--project-workflow)
  - [11. Logging \& observability](#11-logging--observability)
  - [12. Environment variables](#12-environment-variables)
  - [13. Release \& versioning](#13-release--versioning)
  - [14. Tool versions (frozen)](#14-tool-versions-frozen)
  - [15. How to add a new feature (TL;DR)](#15-how-to-add-a-new-feature-tldr)

## 1. Directory conventions

| Path | Purpose |
|------|---------|
| `agent_runtime/` | LangGraph runtime + helpers |
| `memory_service/` | FastAPI service + Kùzu client |
| `mcp_server/` | Mission-Control Plane APIs |
| `tools/` | CLI utilities (`bootstrap.py`, `swarmctl.py`, …) |
| `.devcontainer/` | VS Code container spec |
| `.github/workflows/` | CI/CD actions only (no logic) |
| `docs/` | MkDocs site—one file per topic |
| `tests/` | **mirrors package tree**: `tests/agent_runtime/test_*.py` |

## 2. Coding style

### 2.1 Python

- **Formatter:** `black 25.1.0` (line-length = 88)
  ↳ run by pre-commit; do **not** hand-format code.
- **Linter:** `ruff ^0.4` with the following rule sets **enabled**:
  `E,F,W,I,B,S,UP,NPY,PERF,PL`, plus `RUF100` (annotate all TODOs).
- **Typing:** `pyright` strict mode; every public symbol **must** have explicit type annotations.
- **Imports:** `isort` profile = *black* (handled automatically).
- **Style guide:** Follow [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html) and [PEP 8](https://peps.python.org/pep-0008/).
- **Type checking:** All code must pass `mypy --strict` with no errors.
- **Docstrings:** Google style via `pydocstyle --convention=google`; every public
  function, class, and module **MUST** have docstrings with:

  ```python
  def foo(bar: str) -> str:
      """One-line summary.

      Args:
          bar: Detailed arg description (≤ 1 sentence).

      Returns:
          What the function gives back.

      Raises:
          ValueError: If input is invalid.
      """
  ```

- **Max cyclomatic complexity:** `10 (radon cc --fail B)`
- **Logging:** `use std-lib logging; never print()` outside tests or scripts.
- **Prohibited:** `eval`, `exec`, wildcard imports, mutable default args.

#### 2.1.1 Naming Conventions

- **Classes:** PascalCase

  ```python
  class AgentRuntime:
      """Agent execution environment."""
      pass

  class MemoryService:
      """Service for persistent memory storage."""
      pass
  ```

- **Functions/Methods/Variables:** snake_case

  ```python
  def process_agent_message(message_payload: dict[str, Any]) -> dict[str, Any]:
      """Process an incoming agent message.

      Args:
          message_payload: Dictionary containing message data.

      Returns:
          Processed response dictionary.
      """
      agent_response: dict[str, Any] = {}
      return agent_response
  ```

- **Constants:** UPPER_SNAKE_CASE

  ```python
  MAX_RETRIES: int = 3
  DEFAULT_TIMEOUT: float = 30.0
  API_BASE_URL: str = "https://api.example.com/v1"
  ```

- **Type variable names:** Use CamelCase with a leading `T`

  ```python
  from typing import TypeVar, Generic, Sequence

  TItem = TypeVar("TItem")

  class DataContainer(Generic[TItem]):
      """Container for generic data items.

      Args:
          items: Initial sequence of items.
      """
      def __init__(self, items: Sequence[TItem]) -> None:
          self.items: list[TItem] = list(items)
  ```

- **Private attributes/methods:** Prefix with underscore

  ```python
  class Agent:
      """Base agent class with internal state management."""

      def __init__(self) -> None:
          """Initialize a new agent instance."""
          self._internal_state: dict[str, Any] = {}

      def _validate_input(self, data: dict[str, Any]) -> bool:
          """Internal validation method.

          Args:
              data: Data to validate.

          Returns:
              True if data is valid, False otherwise.
          """
          return True
  ```

- **Unused variables:** Prefix with underscore

  ```python
  # BAD
  for i in range(10):
      print("Hello")

  # GOOD
  for _ in range(10):
      print("Hello")
  ```

#### 2.1.2 Code Organization

- **Import order:** stdlib → third-party → local; alphabetically within groups

  ```python
  # Standard library imports
  import collections
  import json
  import os
  import typing
  from datetime import datetime
  from typing import Any, Dict, List, Optional, Tuple

  # Third-party imports
  import httpx
  import langchain
  from pydantic import BaseModel, Field, validator

  # Local imports
  from agent_runtime.base import BaseAgent
  from memory_service.client import KuzuClient
  ```

- **Import statement Style:** One import per line

  ```python
  # BAD
  import sys, os, time

  # GOOD
  import os
  import sys
  import time
  ```

- **Whitespace:** Follow PEP 8

  ```python
  # BAD - inconsistent spacing
  def foo(x:int = 0,y:str="default")->str:
      return y+str(x)

  # GOOD - consistent spacing
  def foo(x: int = 0, y: str = "default") -> str:
      return y + str(x)
  ```

- **Line length:** 88 characters maximum (enforced by Black)

  ```python
  # BAD - exceeding line length
  result = perform_complex_operation(first_parameter, second_parameter, third_parameter, fourth_parameter, fifth_parameter, sixth_parameter)

  # GOOD - proper line breaks
  result = perform_complex_operation(
      first_parameter,
      second_parameter,
      third_parameter,
      fourth_parameter,
      fifth_parameter,
      sixth_parameter,
  )
  ```

- **Class structure order:**
  1. Class variables and constants
  2. `__init__`
  3. Public methods
  4. Private methods (`_method`)
  5. Magic methods (`__str__`, etc.)

  ```python
  class MemoryManager:
      """Manages agent memory operations.

      Provides an interface for storing, retrieving, and managing
      agent memory with appropriate persistence.
      """

      # Class variables
      DEFAULT_TTL: int = 3600
      MEMORY_TYPES: list[str] = ["episodic", "semantic", "procedural"]

      def __init__(self, client: KuzuClient) -> None:
          """Initialize the memory manager.

          Args:
              client: Kuzu graph database client.
          """
          self.client = client
          self._cache: dict[str, Any] = {}

      def store(self, key: str, value: dict[str, Any]) -> None:
          """Store a value in memory.

          Args:
              key: Unique identifier for the memory.
              value: Data to store.
          """
          self._cache[key] = value
          self._persist(key, value)

      def retrieve(self, key: str) -> dict[str, Any]:
          """Retrieve a value from memory.

          Args:
              key: Unique identifier for the memory.

          Returns:
              The stored data or an empty dict if not found.
          """
          return self._cache.get(key) or self._fetch(key)

      def _persist(self, key: str, value: dict[str, Any]) -> None:
          """Internal method to persist to database.

          Args:
              key: Unique identifier for the memory.
              value: Data to store.
          """
          self.client.insert_node(key, value)

      def _fetch(self, key: str) -> dict[str, Any]:
          """Internal method to fetch from database.

          Args:
              key: Unique identifier for the memory.

          Returns:
              Retrieved data or empty dict if not found.
          """
          return self.client.get_node(key) or {}

      def __len__(self) -> int:
          """Return number of items in memory.

          Returns:
              Count of cached memory items.
          """
          return len(self._cache)
  ```

- **Spacing between methods:** Two blank lines between top-level functions and class definitions,
  one blank line between method definitions.

  ```python
  def top_level_function() -> None:
      """This is a top-level function."""
      pass


  class SomeClass:
      """Example class."""

      def method_one(self) -> None:
          """First method."""
          pass

      def method_two(self) -> None:
          """Second method."""
          pass
  ```

- **Maximum function/method length:** 50 lines (excluding docstrings)
- **Maximum line length:** 88 characters (enforced by Black)
- **Maximum file length:** 500 lines

#### 2.1.3 Error Handling

- **Use specific exception types** instead of bare `except:`

  ```python
  # BAD
  try:
      result = api_call()
  except:
      return None

  # GOOD
  try:
      result = api_call()
  except (ConnectionError, TimeoutError) as e:
      logger.error("API call failed: %s", e)
      return None
  ```

- **Custom exceptions** should inherit from standard exceptions

  ```python
  class AgentSwarmError(Exception):
      """Base exception for all WoodYou errors."""

  class MemoryAccessError(AgentSwarmError):
      """Raised when memory service cannot be accessed."""

      def __init__(self, message: str, service_name: str) -> None:
          """Initialize a memory access error.

          Args:
              message: Error description.
              service_name: Name of the inaccessible service.
          """
          self.service_name = service_name
          super().__init__(f"{message} (service: {service_name})")

  class InvalidAgentConfigError(AgentSwarmError):
      """Raised when agent config is invalid."""
  ```

- **Context managers** for resource cleanup

  ```python
  # BAD
  client = httpx.Client(timeout=10.0)
  try:
      response = client.get(url)
  finally:
      client.close()

  # GOOD
  with httpx.Client(timeout=10.0) as client:
      response = client.get(url)
  # client is automatically closed
  ```

- **Use Optional for nullable types**

  ```python
  # BAD
  def find_agent(agent_id: str) -> dict:
      """Find agent by ID."""
      agent = db.get_agent(agent_id)
      if agent is None:
          return {}
      return agent

  # GOOD
  def find_agent(agent_id: str) -> Optional[dict[str, Any]]:
      """Find agent by ID.

      Args:
          agent_id: ID of the agent to find.

      Returns:
          Agent data if found, None otherwise.
      """
      return db.get_agent(agent_id)
  ```

#### 2.1.4 Type Annotations

- **Use type annotations for all public functions and methods**

  ```python
  # BAD
  def process_items(items, callback=None):
      results = []
      for item in items:
          if callback:
              results.append(callback(item))
          else:
              results.append(item)
      return results

  # GOOD
  from typing import Callable, List, Optional, TypeVar, Any

  T = TypeVar("T")
  R = TypeVar("R")

  def process_items(
      items: list[T],
      callback: Optional[Callable[[T], R]] = None
  ) -> list[Any]:
      """Process a list of items with an optional callback.

      Args:
          items: List of items to process.
          callback: Optional function to call on each item.

      Returns:
          List of processed items.
      """
      results: list[Any] = []
      for item in items:
          if callback:
              results.append(callback(item))
          else:
              results.append(item)
      return results
  ```

- **Use collections.abc for container types**

  ```python
  # BAD
  def calculate_average(numbers: list) -> float:
      return sum(numbers) / len(numbers)

  # GOOD
  from collections.abc import Sequence

  def calculate_average(numbers: Sequence[float]) -> float:
      """Calculate the average of a sequence of numbers.

      Args:
          numbers: Sequence of numbers.

      Returns:
          The arithmetic mean.

      Raises:
          ZeroDivisionError: If the sequence is empty.
      """
      return sum(numbers) / len(numbers)
  ```

- **Use Union for multiple return types**

  ```python
  from typing import Union

  def parse_user_input(text: str) -> Union[int, str, None]:
      """Parse user input into an appropriate type.

      Args:
          text: Input text to parse.

      Returns:
          Integer if input is numeric, original string otherwise,
          or None if input is empty.
      """
      if not text:
          return None
      try:
          return int(text)
      except ValueError:
          return text
  ```

- **Use TypedDict for dictionaries with known structures**

  ```python
  from typing import TypedDict, List

  class AgentConfig(TypedDict):
      """Configuration for an agent."""
      name: str
      capabilities: list[str]
      timeout: float

  def create_agent(config: AgentConfig) -> Agent:
      """Create an agent from configuration.

      Args:
          config: Agent configuration dictionary.

      Returns:
          Configured agent instance.
      """
      return Agent(
          name=config["name"],
          capabilities=config["capabilities"],
          timeout=config["timeout"],
      )
  ```

#### 2.1.5 Comments

- **Use inline comments sparingly** and focus on "why" not "what"

  ```python
  # BAD - explains what (obvious from code)
  x = x + 1  # Increment x

  # GOOD - explains why
  x = x + 1  # Adjust for zero-indexing in the API
  ```

- **TODO comments** must include ticket reference

  ```python
  # TODO(#123): Add support for more authentication methods

  # BAD
  # TODO: Make this better
  ```

- **Comments should be complete statements** with proper capitalization and punctuation

  ```python
  # BAD
  # get user data from database

  # GOOD
  # Get user data from database to populate the profile form.
  ```

#### 2.1.6 Testing

- **Test organization:** One test file per module, matching structure

  ```shell
  my_module/
    __init__.py
    foo.py
    bar.py
  tests/
    my_module/
      test_foo.py
      test_bar.py
  ```

- **Test fixtures** should be in `conftest.py` or explicitly named

  ```python
  # tests/conftest.py
  import pytest
  from unittest.mock import MagicMock
  from typing import Any, Dict

  @pytest.fixture
  def mock_memory_client() -> MagicMock:
      """Create a mock memory client.

      Returns:
          Mock object with predefined behavior.
      """
      client = MagicMock()
      client.get_node.return_value = {"data": "test"}
      return client

  # tests/test_memory.py
  from memory_service.manager import MemoryManager

  def test_retrieve_from_memory(mock_memory_client: MagicMock) -> None:
      """Test retrieving data from memory."""
      manager = MemoryManager(mock_memory_client)
      result = manager.retrieve("test-key")
      assert result == {"data": "test"}
      mock_memory_client.get_node.assert_called_once_with("test-key")
  ```

- **Test naming:** Describe what's being tested and expected behavior

  ```python
  # BAD
  def test_agent():
      pass

  # GOOD
  def test_agent_initialization_with_valid_config_succeeds():
      """Test that agent initializes correctly with valid configuration."""
      pass

  def test_agent_execution_with_invalid_input_raises_value_error():
      """Test that agent execution raises ValueError with invalid input."""
      pass
  ```

- **Mocking standards:** Prefer monkeypatch over patch decorators

  ```python
  # BAD
  @patch('httpx.get')
  def test_api_call(mock_get):
      mock_get.return_value = {"status": "success"}
      result = make_api_call("test")
      assert result["status"] == "success"

  # GOOD
  def test_api_call(monkeypatch):
      """Test API call with mocked response."""
      def mock_get(*args, **kwargs):
          """Mock implementation of httpx.get."""
          return {"status": "success"}

      monkeypatch.setattr(httpx, "get", mock_get)
      result = make_api_call("test")
      assert result["status"] == "success"
  ```

- **Test data management:** Use fixtures or constants module

  ```python
  # tests/constants.py
  from typing import TypedDict, Dict, Any

  class TestUser(TypedDict):
      """Test user data structure."""
      id: int
      name: str

  TEST_USER: TestUser = {"id": 1, "name": "Test User"}

  class TestConfig(TypedDict):
      """Test configuration structure."""
      timeout: int
      retries: int

  SAMPLE_CONFIG: TestConfig = {"timeout": 30, "retries": 3}

  # tests/test_user.py
  from tests.constants import TEST_USER

  def test_process_user():
      """Test user processing functionality."""
      result = process_user(TEST_USER)
      assert result["processed"] is True
  ```

### 2.2 Bash

- `#!/usr/bin/env bash + set -Eeuo pipefail + IFS=$'\n\t'`
- **ShellCheck** `clean (shellcheck -e SC1091 file.sh)`

```bash
#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'

# Example bash script that follows standards
LOG_DIR="${LOG_DIR:-/var/log/WoodYou}"
MAX_RETRIES=3

function log_message() {
    local level="$1"
    local message="$2"
    echo "$(date +%Y-%m-%d\ %H:%M:%S) [$level] $message" >> "$LOG_DIR/script.log"
}

function check_dependency() {
    if ! command -v "$1" &> /dev/null; then
        log_message "ERROR" "Required dependency not found: $1"
        exit 1
    fi
}

# Check dependencies
check_dependency "docker"
check_dependency "poetry"

# Main logic
retry_count=0
while [ $retry_count -lt $MAX_RETRIES ]; do
    if docker-compose up -d; then
        log_message "INFO" "Services started successfully"
        break
    fi

    retry_count=$((retry_count + 1))
    log_message "WARN" "Startup failed, retrying ($retry_count/$MAX_RETRIES)"
    sleep 5
done

if [ $retry_count -eq $MAX_RETRIES ]; then
    log_message "ERROR" "Failed to start services after $MAX_RETRIES attempts"
    exit 1
fi
```

### 2.3 Dockerfiles

- Base image must be an **official** or *distroless* image.
- One RUN `apt-get update && apt-get install … && rm -rf /var/lib/apt/lists/*` layer
- HEALTHCHECK always present.
- Labels:
`org.opencontainers.image.{title,description,source,vcs-ref,created}`

```dockerfile
# Example Dockerfile following standards
FROM python:3.11-slim

LABEL org.opencontainers.image.title="WoodYou MCP Server"
LABEL org.opencontainers.image.description="Mission Control Plane Server for Agent Swarm"
LABEL org.opencontainers.image.source="https://github.com/djh00t/WoodYou"
LABEL org.opencontainers.image.created="2025-04-25"
LABEL org.opencontainers.image.vcs-ref="abcdef123456"

# Install dependencies in a single layer
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install poetry and dependencies
COPY poetry.lock pyproject.toml ./
RUN pip install --no-cache-dir poetry==1.8.2 && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev --no-interaction --no-ansi

# Copy application code
COPY mcp_server/ ./mcp_server/

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/healthz || exit 1

# Run as non-root user
RUN useradd -m appuser
USER appuser

# Start the application
CMD ["python", "-m", "mcp_server.main"]
```

### 2.4 SQL Style

```sql
-- SQL formatting conventions
SELECT
    u.id,
    u.name,
    COUNT(a.id) AS action_count
FROM
    users u
    LEFT JOIN actions a ON u.id = a.user_id
WHERE
    u.active = TRUE
    AND a.timestamp > '2025-01-01'
GROUP BY
    u.id,
    u.name
HAVING
    COUNT(a.id) > 5
ORDER BY
    action_count DESC
LIMIT 100;
```

### 2.5 API Design

- **REST API endpoint naming:**
  - Resource-oriented URLs: `/agents`, `/agents/{id}`, `/agents/{id}/tasks`
  - Use nouns, not verbs: `/agents` (not `/get-agents`)
  - Use plural for collections: `/agents` (not `/agent`)
  - Use standard HTTP methods (GET, POST, PUT, DELETE, PATCH)

```python
# Example FastAPI router following REST conventions
from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/agents", tags=["Agents"])

@router.get("/")
async def list_agents():
    """Get all agents.

    Returns:
        List of agent objects.
    """
    return [{"id": 1, "name": "Agent1"}]

@router.get("/{agent_id}")
async def get_agent(agent_id: int):
    """Get a specific agent by ID.

    Args:
        agent_id: The unique identifier of the agent.

    Returns:
        Agent object.

    Raises:
        HTTPException: If agent not found.
    """
    # Example logic
    if agent_id != 1:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with ID {agent_id} not found"
        )
    return {"id": agent_id, "name": "Agent1"}

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_agent(agent: AgentCreate):
    """Create a new agent.

    Args:
        agent: Agent creation data.

    Returns:
        Created agent object with ID.
    """
    return {"id": 2, "name": agent.name}
```

- **API error response format:**

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Agent with ID 123 not found",
    "details": {
      "agent_id": 123
    }
  }
}
```

### 2.6 Pre-commit configuration

The following `.pre-commit-config.yaml` should be used to ensure consistent code quality:

```yaml
# File: .pre-commit-config.yaml
repos:
-   repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
    -   id: trailing-whitespace
    -   id: end-of-file-fixer
    -   id: check-yaml
    -   id: check-json
    -   id: check-toml
    -   id: check-added-large-files
    -   id: debug-statements
    -   id: check-merge-conflict

-   repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: 'v0.4.1'
    hooks:
    -   id: ruff
        args: [--fix, --exit-non-zero-on-fix]
    -   id: ruff-format

-   repo: https://github.com/psf/black
    rev: 25.1.0
    hooks:
    -   id: black
        language_version: python3.11

-   repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
    -   id: mypy
        args: [--strict, --ignore-missing-imports, --allow-untyped-decorators]
        additional_dependencies: [types-all]

-   repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
    -   id: isort
        args: ["--profile", "black", "--filter-files"]

-   repo: https://github.com/PyCQA/bandit
    rev: 1.7.7
    hooks:
    -   id: bandit
        args: [-ll, --recursive, -i]
        exclude: ^tests/

-   repo: https://github.com/koalaman/shellcheck-precommit
    rev: v0.9.0
    hooks:
    -   id: shellcheck
        args: [--severity=warning]

-   repo: https://github.com/executablebooks/mdformat
    rev: 0.7.17
    hooks:
    -   id: mdformat
        additional_dependencies:
        -   mdformat-gfm
        -   mdformat-black

-   repo: https://github.com/igorshubovych/markdownlint-cli
    rev: v0.38.0
    hooks:
    -   id: markdownlint

# Git secrets for preventing AWS and GitHub tokens
-   repo: https://github.com/awslabs/git-secrets
    rev: master
    hooks:
    -   id: git-secrets
```

Usage:

1. Install pre-commit: `pip install pre-commit`
2. Install git hooks: `pre-commit install`
3. Run on all files: `pre-commit run --all-files`

## 3. Dependency management

- **Package manager:** Poetry; lock file (`poetry.lock`) committed.
- Version pins **MUST** use:

```shell
caret (^)  for libraries          e.g.  requests = "^2.32"
tilde (~)  for tooling/linters    e.g.  black = "~25.1"
git-ref    only if not on PyPI    e.g.  mcp-sdk = {git = "...", rev = "v0.1.3"}
```

- `poetry add` / `poetry remove` only—never edit `pyproject.toml` by hand.
- `make upgrade` (provided) runs `poetry update` + opens a PR with changelog
  using the latest pull request template.

## 4. Security & secrets

| Rule                                      | Enforced by                          |
|-------------------------------------------|--------------------------------------|
| No AWS / GH tokens in repo                | `git-secrets` pre-commit             |
| Bandit severity ≥ MEDIUM, confidence ≥ HIGH | `bandit -r .` in CI                  |
| `cryptography` pinned to latest minor     | Dependabot                           |
| Outbound HTTP MUST use TLS & timeout      | `ruff S` checks                      |
| Secrets loaded from env vars or Vault only | Code review                          |

## 5. Testing

- Framework = `pytest` + `pytest-asyncio` + `pytest-cov`
- **File naming:** `test_<module>.py`, function naming: `test_<unit>_<should>`
- **Coverage:** `pytest --cov=.` must report **≥ 80 % lines AND ≥ 80 % branches**.
- **Property tests:** use `hypothesis` for pure functions with complex inputs.
- **Integration tests** that hit Docker services marked `@pytest.mark.integration`
and run in a separate CI job.
- No skipped tests on main.

## 6. Commit & PR process

### 6.1 Commit messages

- Conventional Commits v1.0 with scope:

```shell
feat(runtime): add skill loader
fix(memory): handle kuzu timeout
docs(readme): clarify bootstrap
refactor(server)!: replace grpc api
```

- The body **MUST** include “Closes #”.
- Emoji allowed **after** type, not before `(feat: 🐛 fix … is wrong)`.

### 6.2 Branches

```shell
feat/<issue-id>
fix/<issue-id>
docs/<slug>
hotfix/<issue-id>
```

### 6.3 Pull-requests

| Checklist item                        | Tool that checks            |
|---------------------------------------|-----------------------------|
| PR title = Conventional Commit        | PR template + CI            |
| All checkboxes in issue description ticked | pr-checklist action         |
| CI status green                       | GitHub branch protection    |
| At least 1 reviewer approval          | Branch protection           |
| No merge conflicts                    | GitHub UI                   |

Squash-merge only. Semantic-release generates tags & changelog.

## 7. Documentation

- **Docs site:** MkDocs-Material (docs/).
- Any new public module/class **MUST** be added to the nav in `mkdocs.yml`.
- **Diagrams:** [draw.io](https://draw.io) → export as SVG → store in `docs/assets/`.
- All Markdown runs through `markdownlint` + `mdformat`.
- `README.md` **MUST** show: quick-start (3 commands), badge table (CI,
  coverage), architecture diagram.

## 8. DevContainer & local setup

1. Install **Docker >= 24** and **VS Code** + *Dev Containers* extension.
2. `git clone` … && `code .` → open in container.
3. On first open, postCreate script runs:

    ```shell
    poetry install
    pre-commit install
    git config commit.gpgsign true
    ```

4. `make init` sets up git hooks & verifies Docker images pull.

## 9. CI/CD pipeline

| Stage              | Job name                          | Blocks merge if fails |
|---------------------|-----------------------------------|-----------------------|
| Lint               | `ruff`                            | ✅                    |
| Format             | `black --check`                   | ✅                    |
| Unit tests         | `pytest -n auto --cov=.`          | ✅                    |
| Coverage gate      | `coverage xml + badge`            | ✅                    |
| Security scan      | `bandit, trivy fs .`              | ✅                    |
| Integration tests  | `pytest -m integration`           | ✅                    |
| SBOM generation    | `cyclonedx-python`                | Warning only          |
| Release            | `semantic-release` (runs only on main) | —                 |

## 10. Issue & Project workflow

- Each GitHub **Issue** follows the template (Story + AC + Test checklist + Deliverables).
- **Status field** on the Project board dictates who works next:

| Status             | Who acts             |
|--------------------|----------------------|
| Tests-In-Progress  | Test-writer agent    |
| Tests-Done         | Dev agent            |
| Dev-In-Progress    | Dev agent            |
| Review             | Human reviewer       |
| Done               | Auto-set by CI       |

- Moving a card left (failing tests) unlocks it for the test-writer again.

## 11. Logging & observability

- Use `structlog` with JSON renderer in prod; human renderer in dev.
- Field set: `timestamp`, `level`, `module`, `event`, `trace_id`.
- No `print` or `bare` logging.
- Health endpoints: `GET /healthz`  → `200` `{"status":"ok"}`.
- All services expose Prometheus metrics at `/metrics`.

## 12. Environment variables

| Variable              | Required | Default | Description               |
|-----------------------|----------|---------|---------------------------|
| `APP_ENV`            | yes      | local   | local / dev / prod        |
| `DATABASE_URL`       | yes      | —       | MySQL URL                 |
| `KUZU_URL`           | yes      | —       | Kùzu http endpoint        |
| `EMBED_MODEL_QUANTIZED` | no      | false   | 8-bit embeddings flag     |
| `A2A_TOKEN`          | yes      | —       | bearer for A2A calls      |

All variables documented in `docs/env.md`.

## 13. Release & versioning

- `semantic-release` config in `release.yml`.
- Tag format: `vMAJOR.MINOR.PATCH`.
- Breaking change (!) in commit bumps MAJOR.
- PyPI and OCI images publish automatically after tag.

## 14. Tool versions (frozen)

| Tool       | Version Pin       |
|------------|-------------------|
| Python     | `3.11.*`          |
| Poetry     | `1.8.*`           |
| Docker     | `28.*`            |
| Black      | `25.1.0`          |
| Ruff       | `≥ 0.4,<0.5`      |
| Bandit     | `≥ 1.7,<1.8`      |
| Node (docs)| `23.*`            |
| Coverage   | `7.8.*`           |
| Trivy      | `v0.18.3`         |
| CycloneDX  | `10.*`            |

## 15. How to add a new feature (TL;DR)

1. `swarmctl list` → copy issue number.
2. `git switch -c feat/<id>-tests` → write failing tests, open PR.
3. Merge tests → board auto-moves to **Tests-Done**.
4. `git switch -c feat/<id>` → code until tests pass.
5. Squash-merge with Conventional Commit title.
6. Semantic-release tags & publishes.

If in doubt, **ask in #WoodYou-dev Slack channel** — better a question than a broken build.
7. Ensure all code adheres to the established coding standards.
