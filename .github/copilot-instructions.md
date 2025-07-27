# Copilot Instructions for Agent-Swarm

GitHub Copilot MUST follow all standards and policies defined in:

- [docs/STANDARDS.md](../docs/STANDARDS.md) (coding style, naming, testing,
  commit/PR process, security, CI, docs)
- [docs/PROJECT_OVERVIEW.md](../docs/PROJECT_OVERVIEW.md) (project structure,
  goals, and terminology)
- [docs/PROJECT_PLAN.md](../docs/PROJECT_PLAN.md) (current tasks, acceptance
  criteria)
- [README.md](../README.md) (quickstart, architecture, usage)

## Key Rules (see STANDARDS.md for full details)

- **Python code:**
  - Use Black (line length 88), Ruff (strict), Pyright (strict), isort (black profile)
  - All public functions/classes MUST have Google-style docstrings
  - Type annotations required everywhere
  - Imports: stdlib → third-party → local, one per line
  - Naming: PascalCase for classes, snake_case for functions/vars,
    UPPER_SNAKE_CASE for constants
  - No print() outside tests/scripts; use logging
  - Max function: 50 lines; max file: 500 lines
  - Tests: pytest, ≥80% coverage, property tests with hypothesis
- **Commits/PRs:**
  - Conventional Commits, squash-merge, PR title = Conventional Commit
  - PRs must pass all CI, have all checkboxes ticked, and no merge conflicts
- **Docs:**
  - All new public modules/classes must be documented in Markdown and added to nav
  - All Markdown must pass markdownlint and mdformat
- **Security:**
  - No secrets in code, use env vars
  - Bandit, git-secrets, and Trivy must pass
- **Devcontainer/VSCode:**
  - Use settings and extensions as defined in .devcontainer and .vscode

## How to Use

- When generating or editing code, always check and apply the rules in
  docs/STANDARDS.md and related docs above.
- If unsure, prefer the strictest interpretation of the standards.
- If a rule is ambiguous, add a TODO with a ticket reference and explain in a comment.

**Never suggest code or changes that would fail CI or violate any MUST/SHALL
rule in docs/STANDARDS.md.**
