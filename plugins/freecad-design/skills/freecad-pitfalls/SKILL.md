---
name: freecad-pitfalls
description: "What goes wrong in FreeCAD's Python API and how to avoid it: import order, building from primitives and booleans, selecting edges by geometry, fillets that fail after booleans. Read before you write or change a part."
---
# FreeCAD pitfalls

## Import order

```python
import FreeCAD as App  # first: `import Part` on its own crashes FreeCAD 1.1
import Part
```

tests/conftest.py imports FreeCAD for the tests already.

## A part module

```python
from dataclasses import dataclass

import FreeCAD as App
import Part


@dataclass(frozen=True)
class Params:
    width_mm: float = 190.0
    depth_mm: float = 190.0
    height_mm: float = 100.0
    wall_mm: float = 2.4
    floor_mm: float = 4.0
    edge_radius_mm: float = 1.0


PARAMS = Params()


def build(p: Params = PARAMS) -> Part.Shape:
    outer = Part.makeBox(p.width_mm, p.depth_mm, p.height_mm)
    inner = Part.makeBox(p.width_mm - 2 * p.wall_mm, p.depth_mm - 2 * p.wall_mm, p.height_mm,
                         App.Vector(p.wall_mm, p.wall_mm, p.floor_mm))
    return outer.cut(inner).removeSplitter()
```

Every dimension comes from Params. Positions are expressions of them, never typed numbers.

## Booleans

- `a.fuse(b).removeSplitter()`: without removeSplitter, seam edges split faces and edges, and
  everything selected afterwards misses.
- Cut holes with cylinders longer than the material (+1 mm each side), so no skin is left.
- `shape.isValid()` after a boolean: an invalid result usually means two faces coincide
  exactly. Make the tool 0.01 mm larger or move it.

## Edges and faces by geometry, never by index

`shape.Edges[7]` is another edge as soon as anything changes. Select by what the edge is:

```python
EPS = 1e-6
vertical = [e for e in shape.Edges if e.BoundBox.XLength < EPS and e.BoundBox.YLength < EPS]
rims = [e for e in shape.Edges if isinstance(e.Curve, Part.Circle) and abs(e.Curve.Radius - r) < EPS]
top = max((f for f in shape.Faces if f.normalAt(0, 0).z > 1 - EPS), key=lambda f: f.BoundBox.ZMax)
```

Raise when a selector finds nothing: an empty list makes makeFillet silently do nothing.

## Fillets and chamfers

- **Round the body first, cut after.** A fillet on a box is easy; the same fillet on the box
  after ten pockets and holes often fails ("BRep_API: command not done"). Build the outer
  shape, fillet its outside edges, then cut the inside.
- If a fillet fails, try in this order: fewer edges at a time, a smaller radius, a chamfer
  (`makeChamfer`), or leave the edge and say so.
- Keep the radius within the room it has: `min(p.edge_radius_mm, p.wall_mm * 0.45)`.

## Look at it

Render after every change (`bash "${CLAUDE_PLUGIN_ROOT}/bin/fc" render <file>`) and compare the pictures with what you meant. A
number that's right in the code can still be the wrong way round on the part.
