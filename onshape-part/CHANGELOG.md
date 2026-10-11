# onshape-part

## v1.4.0

- **Recommended models**: each agent template names the tiers it climbs (`models`, e.g.
  `[fast, strong]`), when it moves up (`escalate_after`) and why (`model_note`). codecrew gives
  an agent made from the template that ladder once the server's tiers have models (Models page);
  before that, and in older codecrews, nothing changes.

## v1.3.0

Onshape moves out of codecrew into this ruleset (codecrew's ruleset hooks).

- **`project_settings`: the Onshape Part Studio** (its URL; context `onshape`, shared with the
  other rulesets that work in Onshape). Asked for on the Projects page; the designer's task names
  it. Projects that had an Onshape document keep it: codecrew moves it into this setting.
- **`guards`: the Onshape design guard**, offered on an agent's page for its Onshape server: only
  Part Studio feature work, only in the project's Part Studio and branch, nothing that writes
  outside code-writing stages, no `file_refs`.
- **`recorders`: `features`** (the feature list, without the fields that change with every
  request, into `design/onshape/features.json`) and **`properties`** (volume, mass and bounding
  box in mm³, g and mm, into `design/onshape/properties.json`, by `properties.py`). Proven by
  `fixtures/recorders/`.
- Needs a codecrew with ruleset hooks: from it on, codecrew records nothing from Onshape for a
  project whose ruleset is older than this version. Older codecrews ignore the sections.

## v1.2.0

- Skills (agents see the list, and load one with `read_skill` when the task touches it):
  `sketch-dimensions` (dimensioning sketches with variables), `feature-status` (checking that a
  feature regenerated, and what to do when it didn't), `api-pitfalls` (units, ids, updates, and
  what codecrew's guard refuses). Needs a codecrew with skills; older versions don't install the folder.

## v1.1.0

- Plan mode: a plan has a parameter table (the variables), interfaces and mating dimensions,
  process limits, targets for size and mass, and the features in order. Plan checks: every
  variable has a unit and a rationale, feature steps reference variables instead of typed-in
  numbers, every variable a feature uses is in the parameter table, no default feature names.
- The designer template starts with plan mode *always ask*: what it builds in Onshape can't be
  undone by git.
- Proven by `fixtures/plans/`. Needs a codecrew with plan mode; older versions ignore the section.

## v1.0.0

Parts designed natively in Onshape. Checks on the recorded feature list: regeneration, dimensions
driven by variables, feature names. Agent templates: Onshape designer, reviewer.
