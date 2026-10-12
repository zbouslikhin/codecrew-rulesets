"""A long pin."""

from dataclasses import dataclass

import FreeCAD as App
import Part


@dataclass(frozen=True)
class Params:
    diameter_mm: float = 6.0
    length_mm: float = 60.0


PARAMS = Params()


def build(p: Params = PARAMS) -> Part.Shape:
    return Part.makeCylinder(p.diameter_mm / 2, p.length_mm)
