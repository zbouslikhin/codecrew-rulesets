# freecad-part

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
