# freecad-part

## v1.4.0

- Skills (agents see the list, and load one with `read_skill` when the task touches it):
  `edges-by-geometry` (selecting edges and faces so fillets survive parameter changes) and
  `import-order` (FreeCAD before Part, and the layout of a part module). Needs a codecrew with skills; older versions don't install the folder.

## v1.3.0

- Permission rules. Denied: `git push`, `git commit`. Needs you (refused for now):
  `pip install` (parts are checked in the toolchain image, not in what an agent installs).
  Allowed, also for agents that only run allowed commands: `python`, read-only git.
- Proven by `fixtures/permissions.yaml`. Needs a codecrew with permission rules; older versions ignore the section.

## v1.2.0

- Plan mode: a plan has a parameter table, interfaces and mating dimensions, process limits,
  targets for size and mass, and its files. Plan checks: every parameter has a unit and a
  rationale and its unit in its name, every new part has a planned test, new files fit the
  structure rules.
- The engineer template starts with plan mode *ask on risk*.
- Proven by `fixtures/plans/`. Needs a codecrew with plan mode; older versions ignore the section.

## v1.1.0

- Generator `part`: the scaffold tool (or `make scaffold`) writes parts/<name>.py and
  tests/test_<name>.py, a skeleton that passes every check; the engineer template has the tool.

## v1.0.1

- Python outside parts/, tests/ and scripts/ is an error (outside-parts), with where it
  belongs: a part in src/parts/ used to pass unchecked.

## v1.0.0

Parametric parts scripted with FreeCAD 1.1 (headless). Engineering checks (contract, units in
parameter names, valid solid, parametric robustness at +/-10%, STEP export, a test per part),
ruff, pytest. Project template (an L-shaped mounting bracket), agent templates (engineer,
reviewer, researcher), toolchain Dockerfile.
