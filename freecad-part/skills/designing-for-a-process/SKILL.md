---
name: designing-for-a-process
description: How to shape a part so its manufacturing process can make it, what the manufacturability checks measure, and what to do about each finding. Read before you model a part, and when a check names a process.
---
# Designing for a process

The spec names how the part is made (`processes`). The built solid is measured and judged by
that process's profile; a part that names two processes must pass both. Decide the process
before the shape: the same function looks different printed, milled, folded and moulded.

The spec's `[orientation]` says how the part lies in the machine: `up = "+z"` (the default) is
the build direction for printing, the tool's axis for milling, the direction of pull for
moulding. Model the part in that orientation, or state another.

## 3D printing, filament (`fdm`)

| Check | Limit | What to do |
|---|---|---|
| `thin-wall` | 0.8 mm | Walls in multiples of the nozzle width; 1.2 mm and up for anything that carries load. |
| `small-hole` | 2 mm | Smaller holes close up: drill them after printing, and say so in the spec's purpose. |
| `overhang` | 45° from vertical | Turn the part so the surface faces up; chamfer the underside at 45° instead of a flat ledge; or split the part. |
| bridges | 10 mm | A flat underside between two supports may span this much. |
| horizontal holes | 8 mm | Larger ones need a teardrop shape or a turned part. |

Put the largest flat face on the bed. Holes that must be round and accurate point up.

## 3D printing, resin and powder (`sla`, `sls`)

`thin-wall` (0.6 / 0.8 mm), `small-hole` (0.5 / 1.5 mm), and `enclosed-void`: a closed cavity keeps
its resin or powder. Give every hollow an opening, two for resin so it drains.

## Milling (`milling`)

| Check | Limit | What to do |
|---|---|---|
| `sharp-internal-corner` | none allowed between two walls | Fillet every corner where two walls meet, with the cutter's radius or more. A wall meeting a floor may be sharp. |
| `tight-internal-corner` | 1 mm radius | Larger radii mean a stiffer, faster cutter: use the largest the function allows. |
| `deep-corner` | 4 cutter diameters | A deep pocket needs a larger corner radius (a longer cutter must be thicker), or less depth. |
| `deep-hole` | 10 diameters | Shorten it, widen it, or drill from both sides. |
| `unreachable` | from above and below | The tool comes along the up axis, then the part is turned over. A slot in the side, or anything under an overhang, needs another setup: restate the design, or add tool directions for this project in `design/processes.toml`. |
| `thin-wall` | 0.8 mm | Thin walls chatter and bend. |

If a mating part has square corners, relieve the pocket's corners (a "dog-bone") instead of
asking for a sharp one.

## Turning (`turning`)

`not-rotational`: every feature is round about one axis. `too-slender`: longer than 6 diameters
needs support. A turned part with a flat or a cross hole is two operations; these checks judge a
part as made by each named process alone, so name the process that makes the whole shape.

## Flat sheet: laser and waterjet (`laser_cutting`)

`not-flat-sheet`: one thickness, cut square through; no pockets, no chamfers. `small-hole`: no
hole smaller than the sheet is thick. `thin-wall`: 1 mm of material between cuts at least.
Declare the thickness in the spec's `[[standards]]` as a `sheet_thickness`.

## Sheet metal, folded (`sheet_metal`)

`tight-bend`: the inside radius of every bend is at least the sheet's thickness; a sharp fold
cracks. Model each bend with its radius. `small-hole` as for flat sheet. Not checked yet: the
distance of holes from bends, and whether the part unfolds flat; keep holes three thicknesses
plus the bend radius away from a bend, and check the flat pattern yourself.

## Injection moulding (`injection_moulding`)

| Check | Limit | What to do |
|---|---|---|
| `no-draft` | 1° | Every face along the direction of pull leans by at least 1°, more for textured faces. Build walls tapered, not straight. |
| `undercut` | none | Every surface must be visible from above or from below. A side hole or a snap hook needs a side action: avoid it, or turn it into a shut-off. |
| `thick-wall` | 4 mm | Thick sections sink. Core them out and use ribs. |
| `thin-wall` | 0.8 mm | The melt doesn't fill thinner. |

Keep the wall even: the same thickness everywhere, with ribs about 60% of it.

## A process of the project's own

`design/processes.toml` may change a process's limits for the project's machines, or define a
new process with the same keys:

```toml
[fdm]
max_size_mm = [220.0, 220.0, 250.0]     # this printer

[die_casting]
title = "Die casting"
materials = ["Aluminium 6061-T6"]
min_wall_mm = 1.5
max_wall_mm = 6.0
min_draft_deg = 1.5
enclosed_voids = false
```

Don't loosen a limit to make a check pass. If the shop really can do better, the limit is
changed there, with a comment saying why; that is the human's call, so raise it in your open
issues.

## When a finding seems wrong

The measurements are geometric rules of thumb. Each message says where (x, y, z) and how much.
Look at that place first: most findings are real. If one isn't (a thin edge that is a deliberate
knife edge, a hole the shop will drill afterwards), don't work around it in the geometry: say so
in your open issues, so the human can decide.
