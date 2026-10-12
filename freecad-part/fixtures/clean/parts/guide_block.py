"""A milled guide block: a bored hole that a bush slides into."""

from dataclasses import dataclass

import FreeCAD as App
import Part


@dataclass(frozen=True)
class Params:
    length_mm: float = 40.0
    width_mm: float = 30.0
    height_mm: float = 16.0
    bore_diameter_mm: float = 16.0


PARAMS = Params()


def bore_centre(p: Params = PARAMS) -> App.Vector:
    """Where the bore's axis meets the underside."""
    return App.Vector(p.length_mm / 2, p.width_mm / 2, 0)


def build(p: Params = PARAMS) -> Part.Shape:
    block = Part.makeBox(p.length_mm, p.width_mm, p.height_mm)
    centre = bore_centre(p)
    bore = Part.makeCylinder(p.bore_diameter_mm / 2, p.height_mm + 2, centre - App.Vector(0, 0, 1))
    return block.cut(bore)
