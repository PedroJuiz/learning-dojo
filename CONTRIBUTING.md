# Contributing

Thanks for your interest in contributing to learning-dojo!

## Adding a new project

1. Create a subfolder (e.g. `my-project/`) with this structure:
   ```
   my-project/
   ├── src/my_project/
   ├── tests/
   ├── pyproject.toml
   ├── CLAUDE.md
   └── README.md
   ```
2. Use `uv` for dependency management. Run all commands from within the project subfolder.
3. Add a `CLAUDE.md` covering setup, commands, and architecture.
4. Add a row to the project tables in both `README.md` and `CLAUDE.md`.

## Development workflow

```bash
# Install dependencies (run from the project subfolder)
uv sync

# Lint and format
uv run ruff check src tests
uv run ruff format src tests

# Type check
uv run mypy src

# Run tests
uv run pytest
```

## Submitting changes

- Branch from `main` using the naming convention: `feature/`, `fix/`, `docs/`, etc.
- One logical change per commit. Follow [Conventional Commits](https://www.conventionalcommits.org/).
- Open a PR against `main`. Fill out the PR template.
- All checks must pass before merging.
