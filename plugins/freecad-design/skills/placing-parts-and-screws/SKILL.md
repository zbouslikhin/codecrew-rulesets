---
name: placing-parts-and-screws
description: "Building an assembly: placing parts from their parameters, reference geometry, and screws with standards.shapes.placed_screw so the head is on the right side. Read before you write or change an assembly."
---
# Placing parts and screws

## The assembly module

```python
import FreeCAD as App
import Part

from parts import tray_tile
from standards import shapes

T = tray_tile.PARAMS


def build() -> dict[str, Part.Shape]:
    out: dict[str, Part.Shape] = {}
    for i in range(5):
        tile = tray_tile.build(T)
        tile.translate(App.Vector(i * T.width_mm, 0, 0))
        out[f"tray_tile:{i + 1}"] = tile
    frame = Part.Shape()
    frame.read("reference/frame.step")
    out["frame"] = frame
    return out
```

- Positions come from the parts' parameters (`i * T.width_mm`), never from typed numbers, so
  the assembly follows when a part changes.
- `shape.translate(...)` and `shape.rotate(centre, axis, degrees)` change the shape itself:
  build a fresh one for every copy.
- Reference geometry (what exists) is read from reference/*.step and named after the file.

## Screws: placed_screw

```python
screw = shapes.placed_screw("ISO 4762 M3x12", seat=App.Vector(x, y, z), toward=App.Vector(1, 0, 0))
out[f"standard:ISO 4762 M3x12:{n}"] = screw
```

- `seat` is the point where the underside of the head bears: on the face the head presses
  against. `toward` is the direction the shank goes, into the parts it holds. The head sits
  on the other side.
- Don't rotate screws by hand: a sign wrong puts the head inside the part it should press on.

## A screw joint, worked out

Joining tile A to tile B across their seam, head inside A, insert in B:

1. **Where the head bears:** the inner face of A's post, where a hex key reaches it from inside
   A. That's `seat`; `toward` points from A into B.
2. **A's side:** a clearance hole through A's post (`fasteners.clearance_hole("M3")`, 3.4 mm).
   If the head would sit in material, the post needs a counterbore, or the seat moves.
3. **B's side:** the insert pocket (see printing-basics), deep enough for the insert.
4. **Length:** A's post thickness plus the insert's length, rounded down to a length that
   exists; the tip must end inside the insert, not past it.
5. **Render with `focus` on the screw** and look: head against A's inner face, shank through
   the seam, tip inside B's pocket, nothing red.

## Check what touches what

The checks report overlaps (an error), and a screw that reaches only one part (a warning).
Render the assembly: overlaps are red, and screws show in blue through what hides them.
