---
name: choosing-a-fit
description: How to tolerance what mates (general tolerances, fit classes like H7/g6, deviations), what each process can hold, and how to state fits and stacks in an assembly so they are checked in the worst case. Read before you give an interface its dimensions, or join two parts.
---
# Choosing a fit

A dimension without a tolerance says nothing about the made part. Everything that mates is
toleranced, and the tolerance must be one the process can hold.

## Three ways to tolerance a parameter

```toml
general_tolerance = "m"            # the whole part: ISO 2768-1, f (fine), m, c (coarse), v

[[tolerances]]
parameter = "bore_diameter_mm"
fit = "H7"                         # an ISO 286 class: this size, this grade

[[tolerances]]
parameter = "slot_width_mm"
upper_mm = 0.2                     # or deviations from the number
lower_mm = 0.0

[[tolerances]]
parameter = "length_mm"
general = "f"                      # or a general class for this one
```

The general tolerance covers every dimension that has no entry of its own. A clearance hole
declared in `[[standards]]` already has its class (ISO 273: H12 fine, H13 medium, H14 coarse).
Every parameter an interface names must be covered by one of these, or the spec check fails
(`interface-tolerance`).

General tolerances, +/- mm:

| Size up to | 3 | 6 | 30 | 120 | 400 |
|---|---|---|---|---|---|
| f | 0.05 | 0.05 | 0.1 | 0.15 | 0.2 |
| m | 0.1 | 0.1 | 0.2 | 0.3 | 0.5 |
| c | 0.2 | 0.3 | 0.5 | 0.8 | 1.2 |
| v | – | 0.5 | 1.0 | 1.5 | 2.5 |

## Fits: make the hole an H, choose the shaft

| You want | Hole / shaft | It behaves like |
|---|---|---|
| runs freely, dirt and heat tolerated | H9 / d9, H8 / e8 | a loose running fit |
| runs, guided | H8 / f7, H7 / f7 | a bearing on a shaft |
| slides by hand, located precisely | H7 / g6 | a sliding fit |
| goes together by hand, no play to speak of | H7 / h6 | a locating fit |
| tapped together, comes apart again | H7 / k6, H7 / js6 | a transition fit |
| pressed in, stays | H7 / n6, H7 / p6 | a press fit |

`from standards import tolerances` gives the numbers: `tolerances.limits("H7", 16)` is
(0.0, 0.018), `tolerances.limits("g6", 16)` is (-0.017, -0.006). The table covers holes H, G,
F, E, D, JS and shafts d, e, f, g, h, js, k, m, n, p, grades IT5 to IT14, sizes up to 500 mm.
Don't use a class outside it.

## What a process holds

A tolerance finer than the process holds fails (`tolerance-too-tight`):

| Process | Holds about | So |
|---|---|---|
| turning | IT6 | shafts to g6, h6, k6 |
| milling, boring | IT7 | bores to H7 |
| injection moulding | IT10 | no H7 without machining |
| laser cutting, resin printing | IT11 | clearance fits only |
| sheet metal, powder printing | IT12 | |
| filament printing | IT13 | general tolerance c or v; nothing presses |

If a finer tolerance is really needed, name the operation that achieves it in the entry:
`achieved_by = "reamed after printing"`. The check then passes and reports it. Don't write that
unless the operation is real and someone will do it: say so in your open issues.

For printed parts that must fit each other, don't reach for fit classes: design the clearance
in. 0.2 mm per side slides, 0.1 mm is snug, and a press fit is a metal insert.

## In an assembly: fits and stacks, worst case

A joint between a hole and a shaft says what fit it must be. The check takes both parts'
tolerances and works out the least and the most clearance (`fit`):

```toml
[[joints]]
a = "spacer_bush:I1"
b = "guide_block:I1"
fit = { hole = "guide_block:bore_diameter_mm", shaft = "spacer_bush:outer_diameter_mm", kind = "clearance", max_clearance_mm = 0.05 }
```

`kind` is clearance (always a gap), interference (always pressed) or transition (either).
`min_clearance_mm` and `max_clearance_mm` narrow it.

A stack is a chain of dimensions that must add up to something: a gap that must stay open, a
part that must stand proud, a lid that must close. List the dimensions with their signs and
the limits of the result; the check adds them at their worst (`stack-up`):

```toml
[[stacks]]
id = "S1"
text = "The bush stands 4 mm proud of the block."
terms = ["+spacer_bush:length_mm", "-guide_block:height_mm"]
min_mm = 3.5
max_mm = 4.5
```

Every dimension in a fit or a stack needs a tolerance in its own part's spec (`untoleranced`).
When a stack fails, tighten the dimension with the widest band first, shorten the chain (fewer
parts in it), or move the nominal. Loosening the limits is the human's call.

Write a stack for every place where the assembly only works if dimensions of several parts
agree. If you can't name one, look again at what closes against what.
