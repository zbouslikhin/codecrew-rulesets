"""Sensor mount: the bracket screwed onto the frame rail.

Two M4 screws go through the base into the rail's tapped holes.

The frame is reference CAD (reference/frame.step): what the bracket must fit. It is placed
from its own geometry, by lining its first tapped hole up with the bracket's first hole, so
the assembly follows both when either changes.
"""

from pathlib import Path

import FreeCAD as App
import Part

from parts import mounting_bracket
from standards import shapes

SCREW = "ISO 4762 M4x12"
FRAME = Path(__file__).resolve().parent.parent / "reference" / "frame.step"
EPS = 1e-6


def hole_centres(shape: Part.Shape) -> list[App.Vector]:
    """Where the vertical holes of a shape are, found by their geometry, in x then y order."""
    found: dict[tuple[float, float], App.Vector] = {}
    for face in shape.Faces:
        surface = face.Surface
        if isinstance(surface, Part.Cylinder) and abs(surface.Axis.z) > 1 - EPS:
            centre = App.Vector(surface.Center.x, surface.Center.y, 0)
            found[(round(centre.x, 6), round(centre.y, 6))] = centre
    return sorted(found.values(), key=lambda v: (v.x, v.y))


def build() -> dict[str, Part.Shape]:
    p = mounting_bracket.PARAMS
    bracket = mounting_bracket.build(p)

    frame = Part.Shape()
    frame.read(str(FRAME))
    first = hole_centres(frame)[0]
    # the frame's first hole under the bracket's first hole, its top face under the base
    frame.translate(
        App.Vector(
            p.hole_edge_distance_mm - first.x,
            mounting_bracket.hole_y(p) - first.y,
            -frame.BoundBox.ZMax,
        )
    )
    # a screw through each hole, its head on the base
    screws = {}
    for n, centre in enumerate(hole_centres(bracket), 1):
        screw = shapes.from_designation(SCREW)
        screw.translate(App.Vector(centre.x, centre.y, p.thickness_mm))
        screws[f"standard:{SCREW}:{n}"] = screw
    above = frame.copy()
    above.translate(App.Vector(0, 0, frame.BoundBox.ZLength + p.thickness_mm + 6.0))
    return {"mounting_bracket": bracket, "frame:1": frame, "frame:2": above, **screws}
