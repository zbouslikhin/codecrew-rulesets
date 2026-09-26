# codecrew-rulesets

Rulesets for codecrew, maintained outside of it. Each folder is one ruleset; each
release is a git tag `<name>@v<major>.<minor>.<patch>`.

| Ruleset | For |
|---|---|
| `svelte-feature` | Svelte 5 + TypeScript apps with the Qlayers feature-folder layout. v2: a test per feature, every feature used (reachability), build must pass |
| `python-service` | Python 3.12 services with uv, src layout: ruff, mypy strict, pytest, vulture (warnings) |

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
  CHANGELOG.md
```

## Releasing

1. Change the ruleset; add a fixture case for every new rule.
2. `codecrew ruleset test <name>` must pass (CI runs it on every push).
3. Update `<name>/CHANGELOG.md`, commit, tag: `git tag <name>@vX.Y.Z && git push --tags`.

A new rule that fails existing projects is a major version.
