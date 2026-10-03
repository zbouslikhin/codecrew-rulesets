---
name: feature-status
description: Reading whether an Onshape feature regenerated, and what to do when it didn't. Read before you add your first feature, and when a feature fails.
---
# Checking feature status

Adding a feature succeeding as a call says nothing about the feature. Onshape accepts a feature
that then fails to regenerate; the run fails later, at the `features` check (`regeneration`), after
you've built five more features on top of it. Check each feature when you make it.

## How

After adding or changing a feature, read the Part Studio's feature list (`getPartStudioFeatures`).
The answer has `features` (the history, in order) and `featureStates`: one entry per feature id.

- `featureStatus: OK` — it regenerated. Go on.
- `INFO` — it regenerated, with a remark. Read it; usually fine.
- `WARNING` — it regenerated, but something is off (a selection resolved to less than you asked
  for). The check reports it as a warning; treat it as a defect and fix it now.
- `ERROR` — it didn't regenerate. Everything after it is built on nothing. Stop and fix it before
  adding anything else.

The entry's message (`statusMsg`, or `statusEnum` when there's no text) says why. Quote it in your
summary when you couldn't resolve it.

## When a feature fails

Work down this list; the first that applies is usually the cause.

1. **A variable it uses doesn't exist yet** or is spelled differently (`#wall` vs `#wall_thickness`).
   Variable features must come before their first use.
2. **Its selection is empty.** The query that should pick the sketch region, face or edge found
   nothing: the sketch isn't closed, or the feature it refers to failed itself. Fix the earlier
   feature first; statuses cascade.
3. **The geometry is impossible at these values.** A fillet larger than the wall, a cut that
   removes everything, a shell thicker than the part. Change the variable's value or the
   expression (`min`-style limits belong in the parameter table's rationale).
4. **Unit missing.** A length expression without a unit (`20` instead of `20 mm`) or with the wrong
   kind (a length where an angle is expected).
5. **Wrong plane or direction.** The sketch is on another plane than you think, so the extrude goes
   away from the part and a "remove" cuts nothing.

Change the failing feature (`updatePartStudioFeature`) rather than deleting and re-adding it:
later features refer to it by id, and a new feature gets a new id.

## Before you finish

Read the feature list one last time and confirm every state is `OK` or `INFO`. codecrew records
this list as `design/onshape/features.json` after your pass; the check judges exactly that.
