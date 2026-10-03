# onshape-part

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
