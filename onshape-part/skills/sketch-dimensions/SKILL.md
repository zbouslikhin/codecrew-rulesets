---
name: sketch-dimensions
description: Dimensioning Onshape sketches with variables so the checks pass and the part stays parametric. Read before you create or change a sketch.
---
# Dimensioning sketches with variables

The `features` check reads every quantity in the recorded feature list. A sketch dimension typed
in as a number fails it (`literal-dimension`), exactly like a typed-in extrude depth. Only `0` and
`90`, `180`, `270`, `360 deg` may stay plain.

## Order of work

1. **Variables first.** One Variable feature (`assignVariable`) per dimension of your plan's
   parameter table, before the first sketch. Give each its value with the unit (`20.2 mm`,
   `12 deg`). Variables are the one place numbers belong.
2. **Sketch geometry is only a first guess.** Entity coordinates in a sketch are plain numbers in
   **metres** (a 20 mm line ends at `0.02`), not expressions. They place the geometry roughly; they
   don't define the design. What defines it are the constraints and dimensions.
3. **Dimension everything with expressions.** Every dimensional constraint (length, distance,
   diameter, radius, angle) takes an expression: write `#slot_width`, `#wall * 2`,
   `#cable_diameter / 2`. An expression counts as driven by a variable as soon as it contains a
   `#name`.
4. **Constrain the rest geometrically.** Coincident, horizontal, vertical, parallel, tangent,
   symmetric, midpoint. A fully defined sketch has no geometry left that the solver may move. Anchor
   it to the origin (a coincident or midpoint constraint to the origin), or it floats.

## What to check after each sketch

Read the feature list and look at the sketch's entry:

- its status is `OK` (see the skill `feature-status`);
- every quantity parameter in its constraints has an `expression` containing `#`;
- there are as many dimensions as your plan's feature row lists variables. A variable you planned
  but didn't use usually means a dimension is still a guess.

## Mistakes that cost a pass

- **Dimension equal to the guess.** Drawing the line at `0.0202` and leaving it undimensioned
  looks right and regenerates, but changing `#slot_width` changes nothing. The robustness of the
  part is the dimension, not the coordinate.
- **Arithmetic with numbers that are dimensions.** `#width - 4 mm` hides a second dimension in the
  expression. If the 4 mm means something (two walls), write `#width - 2 * #wall`. Pure ratios are
  fine: `#height / 2`.
- **Over-constraining.** A dimension on something a geometric constraint already fixes makes the
  sketch fail to solve. Remove the dimension, not the constraint.
- **A variable used before it exists.** A Variable feature placed after the sketch that uses it
  fails to regenerate: order in the history matters.
