"""A plate with a clearance hole for an M3 screw: what a screw clamps."""

from dataclasses import dataclass

import FreeCAD as App
import Part

from standards import fasteners


@dataclass(frozen=True)
class Params:
    width_mm: float = 260.0
    depth_mm: float = 240.0
    thickness_mm: float = 4.0
    hole_mm: float = fasteners.clearance_hole("M3")


PARAMS = Params()


def build(p: Params = PARAMS) -> Part.Shape:
    plate = Part.makeBox(p.width_mm, p.depth_mm, p.thickness_mm)
    hole = Part.makeCylinder(
        p.hole_mm / 2, p.thickness_mm + 2, App.Vector(p.width_mm / 2, p.depth_mm / 2, -1)
    )
    return plate.cut(hole).removeSplitter()
