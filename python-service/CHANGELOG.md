# python-service

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
