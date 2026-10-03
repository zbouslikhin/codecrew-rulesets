# python-service

## v1.4.0

- Skill `module-pattern`: a module and its test in the src layout under mypy strict, with the
  code each starts from. Agents see it in their list of skills and load it with `read_skill`. Needs a codecrew with skills; older versions don't install the folder.

## v1.3.0

- Permission rules. Denied: `uv publish`, `twine`, `git push`, `git commit`. Needs you (refused
  for now): adding or removing a dependency (`uv add`, `uv remove`, `pip install`), writing
  pyproject.toml. Allowed, also for agents that only run allowed commands: `uv sync`, `uv run`,
  the project's own tools, `python`, read-only git.
- Proven by `fixtures/permissions.yaml`. Needs a codecrew with permission rules; older versions ignore the section.

## v1.2.0

- Plan mode: a plan lists its modules, tests and interface changes. Plan checks: every new
  module has a planned test (`module-has-test`), new modules and tests fit the structure rules,
  interface changes make a plan risky ("ask on risk" asks first).
- The Python developer template starts with plan mode *automatic*.
- Proven by `fixtures/plans/`. Needs a codecrew with plan mode; older versions ignore the section.

## v1.1.0

- Repo map: agents get each file's top-level functions and classes up front.

## v1.0.0

Python 3.12 with uv, src layout. ruff (format + lint, SARIF), mypy strict (one JSON
object per line), pytest, vulture as warnings. Tools are added with `uv add --dev`.
Project template and agent templates (Python developer, Python tester).
