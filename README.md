# codecrew-rulesets

Rulesets for codecrew, maintained outside of it. Each folder is one ruleset; each
release is a git tag `<name>@v<major>.<minor>.<patch>`.

| Ruleset | For |
|---|---|
| `svelte-feature` | Svelte 5 + TypeScript apps with the Qlayers feature-folder layout. v2: a test per feature, every feature used (reachability), build must pass |
| `python-service` | Python 3.12 services with uv, src layout: ruff, mypy strict, pytest, vulture (warnings) |
| `freecad-part` | Parametric mechanical parts and assemblies scripted with FreeCAD 1.1 (headless). Every part and assembly starts from a spec (`design/<name>.spec.toml`: purpose, material, process, envelope, interfaces, requirements with what proves each). Checks: the spec is complete and traceable; geometry (valid solid, units, parametric robustness, STEP export, envelope and mass against the spec); standard sizes, fasteners and materials from a shipped library; design for manufacturing (each part measured against the profile of every process it names: 3D printing, milling, turning, sheet metal, laser cutting, injection moulding, or the project's own); tolerances and fits (every interface toleranced, nothing finer than the process holds); assemblies (every part placed, no interference, joints meeting, clearances kept, screws engaged and reachable, fits and stacks of dimensions in the worst case); industrial design for parts people see and touch (no sharp edges, a family of radii, sizes a hand needs, colour and a finish that suits the material); generated deliverables (a drawing, shaded views and a design report per part, a bill of materials per assembly); hand-over to Onshape (the part rebuilt there is proven the same, variable changes come back and are checked, anything else is drift); ruff, pytest. Build its toolchain image once: `docker build -t codecrew-freecad:1.1.3 freecad-part/toolchain` |
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
  ruleset.yaml `generated`  files the ruleset's own checks write (drawings, reports): committed with
                          the work, but not counted as the agent's changes.
  ruleset.yaml `pipelines`  ways of working the ruleset recommends, as pipeline templates built from its
                          agent templates: offered per project, created with a new project.
  fixtures/permissions.yaml  permission rules: attempts (command, read or write) and the verdict
                          each must get. Every rule needs an attempt it decides.
  ruleset.yaml hooks      for a discipline working in a service outside the repo (a CAD service):
                          `project_settings` (values a project gives, e.g. a document's URL; their
                          placeholders fill the rest), `guards` (ready-made MCP guards for an agent's
                          servers), `recorders` (what codecrew reads through the agent's server after
                          each pass and writes into the repo).
  fixtures/recorders/<recorder>/<case>/  input.json (the calls' results) and expect.json (what must be
                          written; none: nothing). Every recorder needs a case.
  CHANGELOG.md
```

## Releasing

1. Change the ruleset; add a fixture case for every new rule.
2. `codecrew ruleset test <name>` must pass (CI runs it on every push).
3. Update `<name>/CHANGELOG.md`, commit, tag: `git tag <name>@vX.Y.Z && git push --tags`.

A new rule that fails existing projects is a major version.

Plan fixtures, permission fixtures and skills alone, without any toolchain: `codecrew ruleset test <n> --static`.
