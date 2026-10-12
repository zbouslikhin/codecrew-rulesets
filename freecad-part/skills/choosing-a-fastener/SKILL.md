---
name: choosing-a-fastener
description: Choosing screws and the holes they need from the standards library, and declaring them in the spec so the checks can hold them to the standard. Read before you add a hole for a screw, or a screw to an assembly.
---
# Choosing a fastener

Take every fastener number from `standards.fasteners`, never from memory. The library ships with
the ruleset (read-only), and the checks compare your parameters with it.

```python
from standards import fasteners

@dataclass(frozen=True)
class Params:
    hole_diameter_mm: float = fasteners.clearance_hole("M4")            # 4.5, ISO 273 medium
    insert_hole_diameter_mm: float = fasteners.tap_drill("M4")          # 3.3, ISO 2306
    counterbore_diameter_mm: float = fasteners.counterbore_diameter("M4")   # 8.0, DIN 974-1
    counterbore_depth_mm: float = fasteners.counterbore_depth("M4")         # 4.6 at least
```

## Which hole

| The screw... | Hole | Function |
|---|---|---|
| passes through this part | clearance hole | `clearance_hole(thread, fit)` |
| screws into this part | tap drill, then tapped | `tap_drill(thread)` |
| has its head sunk into this part | counterbore, plus the clearance hole | `counterbore_diameter`, `counterbore_depth` |

Clearance fit: **medium** unless there's a reason. *Fine* when the screw also locates the part
(little play); *coarse* when holes in two parts must line up despite loose tolerances, as in
printed or welded parts.

## Which screw

- **Size:** as few different sizes in an assembly as you can; one hex key is worth a lot.
- **Length:** the clamped thickness plus the thread engagement, rounded up to a length screws come
  in (`fasteners.SCREW_LENGTHS`: ... 8, 10, 12, 16, 20, 25, 30 ...). There is no 13 or 14.
- **Engagement:** the checks require at least 1 x the diameter in steel, 1.5 x in aluminium and
  2 x in plastics (`materials.get(name).engagement_diameters`). In a printed part, prefer a
  threaded insert or a nut in a pocket to a thread cut into the plastic.
- **Not too long:** a screw longer than its tapped hole is deep runs into solid material; the
  interference check reports that.

## Declare it in the spec

An interface that mates with a thread must have a parameter held to a standard for that thread,
or the spec check fails (`interface-standard`):

```toml
[[interfaces]]
id = "I1"
mates_with = "M4 socket head screws into the frame"
parameters = ["hole_diameter_mm", "hole_edge_distance_mm"]

[[standards]]
parameter = "hole_diameter_mm"
standard = "clearance_hole"     # or tap_drill, counterbore_diameter, counterbore_depth
thread = "M4"
fit = "medium"                  # optional: without it, any of the three series passes
```

A value that isn't the standard's fails (`nonstandard-size`) and the message names what the
standard allows. If the value is deliberate (a hole enlarged for a printed part that prints
undersize), say why in the entry: `reason = "prints 0.2 mm undersize on this printer"`. The check
then passes and reports the reason.

## In an assembly

List each fastener in the assembly's spec by its designation and place it:

```toml
[[parts]]
standard = "ISO 4762 M4x12"
quantity = 2
```

```python
from standards import shapes

screw = shapes.from_designation("ISO 4762 M4x12")   # head underside at the origin, shank along -Z
screw.translate(App.Vector(x, y, top_of_the_hole))
components[f"standard:ISO 4762 M4x12:{n}"] = screw
```

Model a tapped hole at its tap-drill diameter. The screw's shank then overlaps it by exactly the
thread's depth, which the checks read as engagement, not interference. Two things are checked for
every placed screw: enough thread is engaged (`thread-engagement`), and there is room above the
head for the hex key, 25 mm or six diameters along the screw's axis (`no-tool-access`). If a part
is in the way, move the screw, turn it round, or open the part up.

Known designations: ISO 4762 (socket head cap screws, with geometry), ISO 4032 (hex nuts) and
ISO 7089 (washers). Anything else can be listed, with a warning that nothing about it is checked.
