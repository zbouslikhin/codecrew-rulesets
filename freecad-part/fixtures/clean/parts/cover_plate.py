"""A laser-cut cover plate with four screw holes."""

from dataclasses import dataclass

import FreeCAD as App
import Part


@dataclass(frozen=True)
class Params:
    length_mm: float = 80.0
    width_mm: float = 50.0
    thickness_mm: float = 2.0
    hole_diameter_mm: float = 4.5
    hole_inset_mm: float = 6.0


PARAMS = Params()


def build(p: Params = PARAMS) -> Part.Shape:
    plate = Part.makeBox(p.length_mm, p.width_mm, p.thickness_mm)
    for x in (p.hole_inset_mm, p.length_mm - p.hole_inset_mm):
        for y in (p.hole_inset_mm, p.width_mm - p.hole_inset_mm):
            hole = Part.makeCylinder(
                p.hole_diameter_mm / 2, p.thickness_mm + 2, App.Vector(x, y, -1)
            )
            plate = plate.cut(hole)
    return plate.removeSplitter()
