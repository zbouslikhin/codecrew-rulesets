---
name: design-review
description: The checklist for reviewing a mechanical design before it is released, covering what the checks already guarantee and what only a reviewer can judge. Read when you review a part or an assembly.
---
# Design review

The checks have already established a lot. Don't re-do them; spend your attention on what they
can't see. Read in this order: the request and its attachments, the spec
(`design/<name>.spec.toml`), the report and views (`deliverables/<name>/`), then the code.

## What the checks already guarantee

The spec is complete and names what exists; every interface has a toleranced parameter; standard
sizes are standard; the solid is valid and survives its dimensions changing by 10%; the part
stays within its envelope and mass; it passes the manufacturing limits of every process it
names; tolerances are ones the process holds; assemblies have no interference, their joints
meet, their screws engage and can be reached, their fits and stacks hold in the worst case;
touched parts have no sharp edges; every load the spec states is carried with its safety
factor, by hand calculation. If one of these looks violated, that's a finding about the
check, worth saying, but rare.

## What only you can judge

1. **Is it the right part?** Does the spec say what the request asked for, all of it, and
   nothing invented? A requirement the request doesn't support is a finding; so is one it
   implies that the spec lacks.
2. **Does the evidence prove the requirement?** Open each test named in `proven_by`. A test that
   builds the part and asserts it's a solid proves nothing about a hole spacing. A requirement
   proven only by `param:` says the number was written down, not that the geometry has it.
3. **Do the interfaces carry the fit?** For each interface: are the named parameters really the
   ones that decide whether it fits? Is the tolerance one the function needs, neither looser
   nor tighter? A bearing seat on a general tolerance is a finding; so is an H7 nobody needs.
4. **Is the model built on its parameters?** Typed-in numbers in `build()`, edges selected by
   index, positions in an assembly that aren't taken from the parts: each is a finding, with the
   line.
5. **Would the shop agree?** The manufacturability checks are rules of thumb. Look at the views
   for what they miss: a feature that needs a second setup, a wall that passes but will warp, a
   part that could be two simple ones. For sheet metal, holes near bends and whether it unfolds
   aren't checked at all.
6. **What wasn't modelled?** Fasteners listed but not placed, a mating part taken on trust, a
   standard part the library doesn't know (it's a warning in the checks): say what remains
   unverified.
7. **Were limits moved?** Read `design/processes.toml`, `design/ergonomics.toml` and any
   `reason` or `achieved_by` in the spec. Each is a place where a check was told to accept
   something. Is the reason real?
8. **For parts people meet:** work through the six points on the shaded views in
   `designing-for-people`.
9. **Does it carry what it must?** If the part holds, flexes or snaps and the spec has no
   `[[loads]]`, that is a finding. If it has: is the force traceable, is the model the right one
   (a rectangle's height is the side along the load), is the section the smallest one on the
   load path? The calculation is a beam formula: holes, corners, fatigue and creep are yours
   to judge (`checking-strength`).
10. **Open issues.** Has the engineer said what they couldn't decide? Is any of it something
   you can decide, or must it go to the human?

## Findings

Each finding names the part, the feature or the line, what is wrong, and the value or change
you'd make. "Wall too thin" is not a finding; "the rib at x 12, y 0 is 1.0 mm in PETG and
carries the snap load: 1.6 mm" is. Approve only what you would send to the shop.
