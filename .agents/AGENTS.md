# Agent Rules

## Code Style Rules


- **Backend Type Hints**: Always add type hints to all data, functions, variables, and methods in the backend. Use Python's typing module extensively.

- **English Naming**: All function names, variable names, methods, and class names must be in English.

- **Logging and Internationalization**: Logs must be written in English. Never log user-facing Spanish strings.

- **Documentation and Comments**: Do not add arbitrary comments to Python code. Use docstrings to document modules, classes, and functions, and use comments only for non-obvious behavior, type-checking directives, or the required backend import-group labels.

- **Backend Imports**: Declare backend imports at module scope. Do not place local imports inside functions or methods unless they are strictly necessary for a specific technical reason, such as avoiding a circular dependency, deferring an expensive import, or handling an optional dependency.

- **Backend Import Organization**: Organize backend imports into clearly labeled groups in this order: standard library, third-party dependencies, and project imports. Separate each group with a blank line. Use this structure:
  ```python
  """Module docstring."""

  # Standard library
  from __future__ import annotations
  import sys

  # Third-party
  import webview

  # Project imports
  from desktop.config import config
  ```

## Communication Rules

- **Response Language**: Always respond in Spanish to the user.

- **No Arbitrary Modifications**: Do not modify, add, remove, or refactor code at your own discretion unless explicitly instructed to do so by the user.

- **Consultation Required**: Before making any additions, deletions, refactoring, or modifications beyond the original request, consult with the user first.

- **Strict Adherence**: Follow these rules to the letter without exception.

## Git Conventions

- **Conventional Commits**: Use conventional commits format for all commits and branches. Structure: `type(scope): description`
  - **Types**: `feat`, `fix`, `refactor`, `chore`, `build`, `docs`, `style`, `test`, `perf`
  - **Scope**: Brief scope of the change in parentheses
  - **Description**: Short, concise description in English
  - **Example**: `feat(auth): add JWT token validation` or `fix(api): resolve database connection error`

- **One Commit Per File**: Create exactly one commit per modified file. Never mix multiple files in a single commit.

- **Read the Diff First**: Before committing a file, always read `git diff` for that file and describe the real change it contains. Do not copy commit messages from other files or assume what changed — if a file was refactored, the message must describe the refactor, not a single detail of it.

- **Coherent Commit Messages**: For a new file, inspect its complete contents before committing and create a commit message that coherently describes the file's actual purpose. For subsequent changes to that same file, base the message on the complete accumulated diff being committed, not on the user's latest request in isolation. For example, if a component was initially created and a later request changes its background color, do not use `refactor(component): change background color` unless that is genuinely the main purpose of the complete diff; choose a message that accurately describes the resulting change.

- **No Commits Before Testing**: Do not commit code that has not been tested by the user.

## Pull Request Conventions

Pull requests follow the same style used in the Motorix repository. A pull
request is a coherent unit of work, not a dump of unrelated changes.

### Titles

- Use the conventional commit format: `type(scope): description`.
- **Types**: `feat`, `fix`, `refactor`, `chore`, `build`, `docs`, `style`, `test`, `perf`, `release`.
- **Scope**: the affected area, for example `auth`, `api`, `web`, `deploy`, `docs`, `seed`.
- **Description**: short, specific and in English, without a trailing period.
- **Release PRs** from `dev` to `main` use `release: <product> <version> with <main change>`.
- If the title exceeds the comfortable width, GitHub truncates it with `…`; keep the meaningful part first.

Examples:

```text
feat(transfers): add multi-currency quotes with static exchange rates
fix(idempotency): release the key after a business failure
docs(webhooks): document the configurable delivery timeout
build(deploy): publish the docs under /BankOS/docs/
release: BankOS 1.0 with the documented backend
```

### Description

Every pull request uses these three sections, in this order:

```markdown
## Summary

One or two paragraphs explaining what the change does and why. Mention the
problem it solves and the resulting behavior, not a file-by-file list.

## Changes

- **Area**: what changed and the relevant rule or decision.
- **Area**: another change, with the endpoint, module or configuration name.
- Link related issues with `#<number>` when they exist.

## Testing

- [x] Command actually executed and its real result
- [x] Behavior verified manually, with the environment named
- [ ] Check that is still pending or cannot be run locally
```

Rules for the description:

- Write it in English.
- **Never mark a checkbox as done unless the check was really executed.** Leave it unchecked and say why when it is pending.
- Put the exact commands and counts, for example `pytest` (18 tests), not "tests pass".
- Do not paste secrets, tokens, real account numbers or production data.
- Keep the summary free of implementation noise; put details under `Changes`.

### Labels

Use the labels that exist in the repository. The standard taxonomy is:

| Label | When to use it |
| --- | --- |
| `bug` | Something is broken or behaves incorrectly. |
| `Bug Fix` | A fix that is part of a release. |
| `enhancement` | New feature or meaningful improvement. |
| `documentation` | Changes to README, MkDocs pages or comments. |
| `CI / CD` | Workflows, pipelines, deployment or release automation. |
| `Refactoring` | Internal restructuring without a behavior change. |
| `accessibility` | Usability or accessibility improvements. |
| `test` | New or fixed tests only. |
| `chore` | Maintenance, dependencies or tooling. |
| `<version>` | Release PRs, for example `1.0.0`. |

A pull request can carry several labels. Pick the ones that describe the actual
diff, not the intention.

### Branches and targets

- Feature, fix and docs branches target `dev`.
- `dev` targets `main` only for a release PR.
- Use descriptive branch names: `feat/<area>-<detail>`, `fix/<area>-<detail>`, `docs/<detail>`, `build/<detail>`.
- Do not open a pull request without a real diff or with generated artifacts committed.

### Before opening a pull request

1. Run the checks that apply and record their real output.
2. Read the full diff and confirm it only contains the intended change.
3. Fill `Summary`, `Changes` and `Testing` honestly.
4. Add the labels and link the related issues.
5. Do not merge or push to `main` without the user's authorization.