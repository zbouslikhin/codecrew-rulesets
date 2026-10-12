---
name: designing-for-people
description: Industrial design for parts people see and touch (edges, radii, sizes a hand needs, colour and finish), and the checklist a reviewer uses on the shaded views. Read before you model a part someone handles or looks at, and when you review one.
---
# Designing for people

A part can work and still be unpleasant to hold or look at. Say in the spec whether people
meet it; the checks then hold it to what can be measured, and a reviewer judges the rest.

```toml
[appearance]
visible = true          # someone sees it in use
touched = true          # a hand touches it
colour = "RAL 7016"     # required when visible
finish = "anodised"     # required when visible; must suit the material
rests_on = "-z"         # the face it sits on: its edges may stay sharp

[[grips]]               # what a hand holds, and how
parameter = "diameter_mm"
kind = "power_grip"
```

A spec without `[appearance]` gets a warning: nothing here can be applied to it. A part inside a
machine that nobody sees or touches says `visible = false` and `touched = false`.

## Edges (`sharp-edge`)

A touched part has no sharp outer edge: every outside edge is broken by a radius or a chamfer.
An edge counts as sharp when its two faces turn by 60° or more; a 45° chamfer or a tangent
radius passes. Inside corners don't count: a finger doesn't reach them.

- Break edges last, after the booleans (see `edges-by-geometry`), and select them by geometry.
- 0.5 mm is enough to take the bite off; 1 to 2 mm reads as designed.
- A printed part: chamfer the edges on the bed, round the ones above (a radius on the bed is an
  overhang).
- A moulded part: radius outside edges by the wall thickness plus the inside radius, so the wall
  stays even.
- The face the part sits on keeps its sharp edges if the spec says `rests_on`.

## Radii (`radius-family`)

A visible part uses three different radii or fewer. One for edge breaks, one for corners, one
for the main form is the usual family. Four corners with four radii read as four decisions.
Take the radii from `standards.sizes.RADII`. If the function really needs more, raise
`max_radii` in `[appearance]` and say why in the purpose.

## What a hand holds (`grip-size`)

| Kind | What the parameter is | Range, mm |
|---|---|---|
| `power_grip` | diameter of a handle the whole hand closes around | 30 to 45 |
| `grip_length` | length of a handle for one hand | at least 100 |
| `pinch_grip` | diameter or thickness held between thumb and fingertips | 8 to 16 |
| `finger_hole` | diameter of a hole for one finger | at least 25 |
| `hand_opening_width` | length of an opening the hand goes through | at least 110 |
| `hand_opening_depth` | its clear depth for the fingers | at least 45 |
| `push_button` | diameter of a button pressed with a fingertip | at least 12 |

These are guideline values for adult hands without gloves. Declare every feature a hand holds;
the check can't find them for you. For gloves, children or a specific standard, the project
sets its own ranges in `design/ergonomics.toml` (same keys): that's the human's call.

## Colour and finish

Colour is a name someone can order by: a RAL or Pantone number, or "natural". Finish is one the
library knows, so it can be checked against the material (`finish-material`):

| Finish | For |
|---|---|
| as printed; sanded and painted; vapour smoothed (ABS, ASA) | printed plastics |
| as moulded, textured; as moulded, polished | moulded plastics |
| as machined | milled and turned parts |
| as cut, deburred | laser-cut and sheet-metal parts |
| bead blasted; brushed; polished; powder coated | metals |
| anodised; hard anodised | aluminium |
| zinc plated; black oxide | steel |
| passivated | stainless steel |

A finish adds thickness: anodising and powder coat change fits. Tolerance the dimension that
matters for after the finish, and say so in the tolerance's `achieved_by` or the purpose.

## What a reviewer checks on the shaded views

`deliverables/<part>/views.svg` shows the part from two fixed corners, the same for every part.
Numbers can't judge these; look, and say what you see in a finding:

1. **Proportion.** Does any dimension look arbitrary next to the others? Walls, ribs and
   bosses of similar function should look alike.
2. **One language.** Edges broken the same way throughout; radii that belong together; holes and
   slots aligned to each other or clearly not.
3. **Honest form.** Does the shape show how the part is made and what it does? A printed part
   that imitates a machined one, or decoration with no function, is a finding.
4. **The parts together.** In an assembly: do neighbours share edges, radii and finish? Does a
   screw head sit where a hand or an eye lands?
5. **What a hand meets.** Where is it picked up? Is that where it is rounded and sized for a
   hand, and declared in `[[grips]]`?
6. **The first read.** From across the room: is it clear which way up it goes, and where it is
   operated?

A finding names the feature and what would be better, like any other review finding.
