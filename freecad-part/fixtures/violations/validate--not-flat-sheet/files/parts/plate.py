"""A plate with a recess."""

from dataclasses import dataclass

import FreeCAD as App
import Part


@dataclass(frozen=True)
class Params:
    length_mm: float = 60.0
    width_mm: float = 40.0
    thickness_mm: float = 2.0
    recess_mm: float = 10.0
    recess_depth_mm: float = 1.0


PARAMS = Params()


def build(p: Params = PARAMS) -> Part.Shape:
    plate = Part.makeBox(p.length_mm, p.width_mm, p.thickness_mm)
    recess = Part.makeBox(
        p.recess_mm,
        p.recess_mm,
        p.recess_depth_mm,
        App.Vector(5, 5, p.thickness_mm - p.recess_depth_mm),
    )
    return plate.cut(recess)
