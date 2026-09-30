from dataclasses import dataclass

import FreeCAD as App  # noqa: F401
import Part


@dataclass(frozen=True)
class Params:
    length: float = 10.0
    diameter_mm: float = 8.0


PARAMS = Params()


def build(p: Params = PARAMS) -> Part.Shape:
    return Part.makeCylinder(p.diameter_mm / 2, p.length)
