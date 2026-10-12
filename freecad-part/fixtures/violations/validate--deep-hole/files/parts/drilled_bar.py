"""A bar with a long blind hole."""

from dataclasses import dataclass

import FreeCAD as App
import Part


@dataclass(frozen=True)
class Params:
    side_mm: float = 20.0
    length_mm: float = 60.0
    hole_diameter_mm: float = 3.0
    hole_depth_mm: float = 50.0


PARAMS = Params()


def build(p: Params = PARAMS) -> Part.Shape:
    bar = Part.makeBox(p.side_mm, p.side_mm, p.length_mm)
    hole = Part.makeCylinder(
        p.hole_diameter_mm / 2,
        p.hole_depth_mm + 1,
        App.Vector(p.side_mm / 2, p.side_mm / 2, p.length_mm - p.hole_depth_mm),
    )
    return bar.cut(hole)
