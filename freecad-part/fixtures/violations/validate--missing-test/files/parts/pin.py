from dataclasses import dataclass

import FreeCAD as App  # noqa: F401
import Part


@dataclass(frozen=True)
class Params:
    diameter_mm: float = 3.0
    length_mm: float = 12.0


PARAMS = Params()


def build(p: Params = PARAMS) -> Part.Shape:
    return Part.makeCylinder(p.diameter_mm / 2, p.length_mm)
