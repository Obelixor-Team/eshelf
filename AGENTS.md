# Agents Guide: eshelf

## Developer Commands
- `make run`: Run the application (`src/main.py`)
- `make test`: Run tests with coverage (min 80% required)
- `make lint`: Ruff check (with `--fix`) and format
- `make typecheck`: Mypy strict type checking
- `make pre-commit`: Run all pre-commit hooks
- `make clean`: Clean cache files

## Toolchain & Conventions
- **Python Version**: 3.11
- **UI Framework**: PyGObject (GTK)
- **Package Manager**: `uv`
- **Linting/Formatting**: `ruff` using Google docstring convention
- **Type Checking**: `mypy` in strict mode
- **Commits**: Conventional Commits via `commitizen`
- **Formatting**: Use Unicode characters instead of LaTeX for symbols (e.g., use → instead of $\rightarrow$)

## Architecture
- **Entry point**: `src/main.py`
- **Layers**: `ui` → `controller` → `services` → `database`/`models`
- **Source**: `src/`
- **Tests**: `tests/` (mirrors `src/` structure)

## Verification Workflow
Run in order: `make lint` → `make typecheck` → `make test`

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **eshelf** (852 symbols, 1378 relationships, 8 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> If any GitNexus tool warns the index is stale, run `npx gitnexus analyze` in terminal first.

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `gitnexus_impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user.
- **MUST run `gitnexus_detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows.
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits.
- When exploring unfamiliar code, use `gitnexus_query({query: "concept"})` to find execution flows instead of grepping. It returns process-grouped results ranked by relevance.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `gitnexus_context({name: "symbolName"})`.

## Never Do

- NEVER edit a function, class, or method without first running `gitnexus_impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `gitnexus_rename` which understands the call graph.
- NEVER commit changes without running `gitnexus_detect_changes()` to check affected scope.

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/eshelf/context` | Codebase overview, check index freshness |
| `gitnexus://repo/eshelf/clusters` | All functional areas |
| `gitnexus://repo/eshelf/processes` | All execution flows |
| `gitnexus://repo/eshelf/process/{name}` | Step-by-step execution trace |

## CLI

| Task | Read this skill file |
|------|---------------------|
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md` |

<!-- gitnexus:end -->
