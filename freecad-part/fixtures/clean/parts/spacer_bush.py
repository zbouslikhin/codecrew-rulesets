"""A turned spacer bush with a through bore."""

from dataclasses import dataclass

import FreeCAD as App
import Part


@dataclass(frozen=True)
class Params:
    outer_diameter_mm: float = 16.0
    bore_diameter_mm: float = 8.4
    length_mm: float = 20.0


PARAMS = Params()


def build(p: Params = PARAMS) -> Part.Shape:
    bush = Part.makeCylinder(p.outer_diameter_mm / 2, p.length_mm)
    bore = Part.makeCylinder(p.bore_diameter_mm / 2, p.length_mm + 2, App.Vector(0, 0, -1))
    return bush.cut(bore)
