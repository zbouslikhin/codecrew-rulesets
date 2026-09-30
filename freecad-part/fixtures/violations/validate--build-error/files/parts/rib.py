from dataclasses import dataclass

import FreeCAD as App  # noqa: F401
import Part


@dataclass(frozen=True)
class Params:
    length_mm: float = 30.0
    height_mm: float = 8.0


PARAMS = Params()


def build(p: Params = PARAMS) -> Part.Shape:
    slope = p.height_mm / (p.length_mm - p.length_mm)
    return Part.makeBox(p.length_mm, 2.0, p.height_mm * slope)
