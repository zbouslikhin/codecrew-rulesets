---
name: edges-by-geometry
description: Selecting edges and faces by their geometry instead of their index, for fillets, chamfers and holes that survive parameter changes. Read before you fillet, chamfer or pick a face.
---
# Selecting edges and faces by geometry

`shape.Edges[7]` is edge 7 only for today's dimensions. Change a parameter, add a hole, or fuse in
another order, and edge 7 is a different edge (FreeCAD's topological naming problem). The
`validate` check rebuilds every part with each dimension changed by 10%: a fillet on an index
either lands on the wrong edge or fails, and the part is refused as `not-parametric`.

Select by what the edge **is**: where it lies, which way it runs, how long it is, its radius.

## Patterns

A straight edge at a known position, running along X (the inner corner of an L-bracket):

```python
EPS = 1e-6

def inner_corner(shape: Part.Shape, p: Params) -> Part.Edge:
    for edge in shape.Edges:
        bb = edge.BoundBox
        if (
            abs(bb.YMin - p.thickness_mm) < EPS and abs(bb.YMax - p.thickness_mm) < EPS
            and abs(bb.ZMin - p.thickness_mm) < EPS and abs(bb.ZMax - p.thickness_mm) < EPS
            and abs(bb.XLength - p.width_mm) < EPS
        ):
            return edge
    raise ValueError("inner corner edge not found")
```

All vertical edges (the corners of a plate, to round them):

```python
def vertical_edges(shape: Part.Shape) -> list[Part.Edge]:
    return [e for e in shape.Edges if e.BoundBox.XLength < EPS and e.BoundBox.YLength < EPS]
```

Circular edges of a given radius (the rims of the M4 holes):

```python
def hole_rims(shape: Part.Shape, diameter_mm: float) -> list[Part.Edge]:
    return [
        e for e in shape.Edges
        if isinstance(e.Curve, Part.Circle) and abs(e.Curve.Radius - diameter_mm / 2) < EPS
    ]
```

The top face (largest Z, facing up):

```python
def top_face(shape: Part.Shape) -> Part.Face:
    up = [f for f in shape.Faces if f.normalAt(0, 0).z > 1 - EPS]
    return max(up, key=lambda f: f.BoundBox.ZMax)
```

## Rules that keep it working

- **Express positions with the parameters**, never with the numbers they have today:
  `p.thickness_mm`, not `3.0`.
- **Compare with a tolerance** (`EPS`), not `==`: coordinates are floats.
- **Raise when nothing matches.** A selector that returns an empty list makes `makeFillet` do
  nothing, silently; the part then passes with a sharp corner. `raise ValueError` names the
  problem at the +10% build instead.
- **Select after `removeSplitter()`.** A fuse leaves seam edges that split one real edge into
  two; your length test then matches neither.
- **Limit the fillet to the room it has**: `radius = min(p.fillet_radius_mm, p.thickness_mm * 0.9,
  distance_to_hole - 0.5)`. A fillet that reaches a hole or exceeds a wall fails at -10%.
- **Fillet late.** Each fillet adds faces and edges; selectors written for the unfilleted shape
  stop matching afterwards. Booleans first, fillets and chamfers last.

## Test it

In the part's test, build at the nominal values and at a changed one, and assert what the fillet
was for (the inner corner has no sharp edge; the volume grew by roughly the fillet's section times
the width). A selector is only proven by a build where the numbers differ.
