---
name: printing-basics
description: "What FDM printing asks of a part: walls, overhangs, holes, clearances, heat-set inserts, and splitting parts to fit the bed. Read before you model a printed part."
---
# Printing basics (FDM)

The checks warn about thin walls, overhangs and small holes; only a part larger than the bed is
an error. These numbers keep the warnings away.

| What | Value |
|---|---|
| Wall | at least 0.8 mm (2 lines of a 0.4 mm nozzle); 1.6 to 2.4 mm for a part that carries load |
| Overhang | up to 45° from vertical prints without support |
| Hole on its side | up to 8 mm round; above that, a teardrop (a 45° point on top) |
| Bridge | up to 10 mm |
| Clearance between printed parts that fit together | 0.2 to 0.3 mm per side |
| Clearance hole M3 / M4 / M5 | 3.4 / 4.5 / 5.5 mm (`fasteners.clearance_hole`) |
| Head counterbore M3 | 6.5 mm, 3.4 mm deep (`fasteners.counterbore_diameter`, `counterbore_depth`) |

## Heat-set inserts

A brass insert melted into a printed hole: a metal thread that survives being screwed often.
For the common M3 insert (outer about 4.6 mm, 5.7 mm long):

- hole 4.0 mm, at least 6.5 mm deep (the insert's length plus a little for melted plastic)
- at least 1.6 mm of wall around the hole, so 7.2 mm of material across
- the screw's tip ends inside the insert: screw length = what it clamps + 4 to 5 mm

Check the insert's datasheet when the person names a brand; their numbers win.

## Orientation

The part lies on its largest flat face (`RESTS_ON = "-z"` by default). Model it in the
orientation it prints in, or say which face goes down. Layers are weakest across: a part loaded
in bending is stronger with its layers along the load.

## Too large for the bed

The bed is in design/printer.toml. A part that doesn't fit in any orientation is split, and
how it splits is the person's decision: ask with the options (where the seam goes, how the
pieces join: screws into inserts, a dovetail, glue).
