# codecrew-rulesets

Rulesets for codecrew, maintained outside of it. Each folder is one ruleset; each
release is a git tag `<name>@v<major>.<minor>.<patch>`.

| Ruleset | For |
|---|---|
| `svelte-feature` | Svelte 5 + TypeScript apps with the Qlayers feature-folder layout. v2: a test per feature, every feature used (reachability), build must pass |
| `python-service` | Python 3.12 services with uv, src layout: ruff, mypy strict, pytest, vulture (warnings) |
| `freecad-part` | Parametric mechanical parts scripted with FreeCAD 1.1 (headless): geometry checks (valid solid, units, parametric robustness, STEP export), ruff, pytest. Build its toolchain image once: `docker build -t codecrew-freecad:1.1.3 freecad-part/toolchain` |
| `onshape-part` | Parts designed natively in Onshape, with history: checks on the recorded feature list (regeneration, dimensions driven by variables, feature names) |

## Using one

```bash
codecrew ruleset versions --source https://github.com/zbouslikhin/codecrew-rulesets.git
codecrew ruleset add /path/to/repo --name svelte-feature --version v1.1.0 [--path app/]
```

codecrew copies the files into the repo and pins them in `.codecrew/rulesets.lock`.
Agents can't change them, and a changed file fails the checks. Updates go through
`codecrew ruleset update` or the dashboard's Rulesets page, as a reviewable change.

## Layout of a ruleset

```
<name>/
  ruleset.yaml            checks, structure rules, setup, preview, summary for agents
  files/                  config files installed into the ruleset's folder of the repo
  dev-dependencies.json   packages merged into that folder's package.json (npm only; or use `install`)
  template/               the starting project for `codecrew new-project` ({{name}}, {{module}})
  fixtures/clean/         a project that must pass
  fixtures/violations/*/  files/ laid over clean + expect.yaml: the rule that must catch it
  fixtures/plans/         plan mode: clean.yaml (a plan that must pass) and violations/<case>.yaml
                          (`change`: parts of the clean plan to replace; `expect`: the plan checks
                          that must catch it). Every plan check needs a case.
  skills/<name>/SKILL.md  know-how for the stack: a header (name, description) and the text. Agents
                          get the list and load a skill with read_skill when the task touches it.
  fixtures/permissions.yaml  permission rules: attempts (command, read or write) and the verdict
                          each must get. Every rule needs an attempt it decides.
  CHANGELOG.md
```

## Releasing

1. Change the ruleset; add a fixture case for every new rule.
2. `codecrew ruleset test <name>` must pass (CI runs it on every push).
3. Update `<name>/CHANGELOG.md`, commit, tag: `git tag <name>@vX.Y.Z && git push --tags`.

A new rule that fails existing projects is a major version.

Plan fixtures, permission fixtures and skills alone, without any toolchain: `codecrew ruleset test <n> --static`.
