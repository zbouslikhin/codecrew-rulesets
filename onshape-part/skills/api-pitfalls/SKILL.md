---
name: api-pitfalls
description: What goes wrong when driving Onshape through its API, and how codecrew's guard reacts. Read when a call is refused or behaves unexpectedly.
---
# Onshape API pitfalls

Read the server's own guidance first (`onshape_mcp_get_started` and its resources): it knows the
exact request shapes. This skill is about what bites even when the shape is right.

## Calls codecrew refuses

Calls go through codecrew's design guard before they reach Onshape. A refusal names what was
wrong; don't retry the same call.

- **Only this Part Studio.** Document, workspace and element must be the ones in your task
  (`did`, `wvm: w` with the workspace id, `eid`). Versions (`v`) and microversions (`m`) are
  read-only in Onshape anyway; the guard wants the workspace.
- **Only Part Studio feature operations**: reading features, feature specs, mass properties,
  bounding boxes and parts; adding, updating and deleting features. Anything else (documents,
  assemblies, drawings, exports, sharing) is refused, and the refusal lists what is allowed.
- **Writing only in stages that write.** While planning or reviewing, the operations that change
  the design are refused. Plan them; build them once the plan is approved.
- **No local files.** Arguments that make the server read a file into the request (`file_refs`)
  are refused.

## Units

- Expressions in parameters are strings with units: `"20 mm"`, `"12 deg"`, `"#wall * 2"`.
- Raw sketch geometry (points, line ends, circle radii in entity definitions) is in **metres**
  and radians, without a unit. 20 mm is `0.02`. A sketch that comes out a thousand times too large
  was given millimetres.
- Mass properties and bounding boxes come back in SI: metres, kilograms. Convert before comparing
  them with your plan's targets in mm and g.

## Ids and references

- A feature gets its `featureId` from Onshape when it's added: take it from the answer. Don't
  invent ids, and don't reuse one after deleting its feature.
- Later features refer to earlier ones by id (the sketch an extrude uses). Updating a feature
  keeps its id; deleting and re-adding breaks every reference to it.
- Refer to geometry by what created it (the sketch's region, the faces a feature made), not by
  ids of faces or edges you read off once: those change when anything upstream changes.

## Updating features

- An update sends the whole feature definition, not a patch: read the feature, change what
  changes, send it all back. Parameters you leave out are gone.
- Feature lists carry bookkeeping that changes with every request (microversion, serialization
  version). Send back what the last read gave you; a stale one is rejected. codecrew leaves these
  fields out of the recorded snapshot, so they never show up as a diff.

## Names

Every feature gets a name saying what it's for (`Mounting holes`, not `Extrude 3`): set it when
you add the feature. A default name is a warning in the checks and a finding for the reviewer.

## One feature at a time

Add a feature, read its status, then the next. A batch of ten features with the second one
failing leaves nine statuses to untangle.
