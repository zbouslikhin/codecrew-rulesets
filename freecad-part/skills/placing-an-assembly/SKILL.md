---
name: placing-an-assembly
description: How to build an assembly module (assemblies/<name>.py) so parts are placed by their interfaces and the interference, joint and clearance checks pass. Read before you assemble parts.
---
# Placing an assembly

An assembly is `assemblies/<name>.py` with `build()` returning its placed components as a dict,
name to `Part.Shape`, each already where it belongs. Its spec (`design/<name>.spec.toml`) lists
the parts and the joints; the checks compare the two.

```python
def build() -> dict[str, Part.Shape]:
    p = mounting_bracket.PARAMS
    bracket = mounting_bracket.build(p)
    frame = Part.Shape()
    frame.read(str(FRAME))                      # reference CAD: what it must fit
    first = hole_centres(frame)[0]
    frame.translate(App.Vector(
        p.hole_edge_distance_mm - first.x,      # its first hole under the bracket's
        mounting_bracket.hole_y(p) - first.y,
        -frame.BoundBox.ZMax,                   # its top face under the base
    ))
    return {"mounting_bracket": bracket, "frame": frame}
```

## Names

| In the spec | Key in build() |
|---|---|
| `part = "link"`, quantity 1 | `"link"` |
| `part = "pin"`, quantity 3 | `"pin:1"`, `"pin:2"`, `"pin:3"` |
| `reference = "reference/frame.step"` | `"frame"` (the file's name without extension) |
| `standard = "ISO 4762 M4x12"` | needn't be placed; if you do, `"standard:ISO 4762 M4x12:1"` |

A part the spec lists but `build()` doesn't place fails (`component-missing`), as does one placed
that the spec doesn't know (`component-unknown`).

## Place from the parts, not from numbers

A typed-in offset is right until a parameter changes. Take positions from where they come from:

- **the part's own parameters and helpers**: `p.hole_edge_distance_mm`, `mounting_bracket.hole_y(p)`.
  If a position is computed inside `build()` of the part, move it into a helper function and use
  it in both places;
- **the geometry of reference CAD**: find its holes, faces and edges by what they are (a
  cylindrical face with a vertical axis, the top face), as in the skill `edges-by-geometry`;
- **bounding boxes** for "on top of", "flush with": `-frame.BoundBox.ZMax`.

Move a shape with `shape.translate(App.Vector(...))` and `shape.rotate(centre, axis, degrees)`.
`build()` of a part returns a new shape each time, so moving it doesn't disturb the part.

## What the checks measure

- **Interference:** no two components may share volume. The message says which two, how much,
  and where. Usual causes: a clearance that is in the spec but not in the parameters, a part
  placed by its corner instead of its mating face, a hole smaller than what goes through it.
- **Fixed joints meet:** the two sides of a joint are at most 0.5 mm apart, or the joint's
  `max_gap_mm`. A joint that is open means the parts aren't where the spec says they join.
- **Moving joints clear:** a joint with `kind = "sliding"` or `"rotating"` needs `clearance_mm`,
  and its two sides must be at least that far apart, everywhere.

```toml
[[joints]]
a = "slider:I1"
b = "rail:I1"
kind = "sliding"
clearance_mm = 0.3      # the gap the printed parts need to move
```

## Test what matters

Every assembly has `tests/test_<name>.py`. Test the facts of the fit, not the code: the holes of
one part line up with the holes of the other; the mating faces touch; what moves has room across
its travel (build the moving part at both ends and check both).
