"""A printed block with a vent hole."""

from dataclasses import dataclass

import FreeCAD as App
import Part


@dataclass(frozen=True)
class Params:
    size_mm: float = 20.0
    height_mm: float = 6.0
    hole_diameter_mm: float = 1.0


PARAMS = Params()


def build(p: Params = PARAMS) -> Part.Shape:
    block = Part.makeBox(p.size_mm, p.size_mm, p.height_mm)
    return block.cut(
        Part.makeCylinder(
            p.hole_diameter_mm / 2, p.height_mm + 2, App.Vector(p.size_mm / 2, p.size_mm / 2, -1)
        )
    )
