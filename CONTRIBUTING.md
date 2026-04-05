# Contributing

Thanks for your interest in contributing to learning-dojo!

## Adding a new project

Each project lives in its own subfolder. The structure will vary by language, but every project must have:

```
my-project/
├── src/          # or the language-idiomatic source layout
├── tests/
├── CLAUDE.md     # setup, commands, architecture
└── README.md     # what the project does and how to run it
```

### Requirements for any new project

1. Self-contained — all dependencies declared and installable from the subfolder.
2. Tested — include a test suite runnable with a single command.
3. Documented — `README.md` explains the purpose and how to get started; `CLAUDE.md` covers setup, commands, and architecture for Claude Code users.
4. Listed — add a row to the project tables in both the root `README.md` and `CLAUDE.md`.

### Language-specific notes

| Language | Dependency manager | Lint/format | Tests |
|---|---|---|---|
| Python | `uv` | `ruff` | `pytest` |
| TypeScript/JS | `npm` / `pnpm` | `eslint` + `prettier` | `vitest` / `jest` |
| Other | Use the idiomatic tool | — | — |

Run all commands from within the project subfolder, not the repo root.

## Submitting changes

- Branch from `main` using the naming convention: `feature/`, `fix/`, `docs/`, etc.
- One logical change per commit. Follow [Conventional Commits](https://www.conventionalcommits.org/).
- Open a PR against `main`. Fill out the PR template.
- All checks must pass before merging.
