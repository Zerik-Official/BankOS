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