from dataclasses import dataclass

import FreeCAD as App  # noqa: F401
import Part


@dataclass(frozen=True)
class Params:
    outer_mm: float = 10.0
    height_mm: float = 2.0


PARAMS = Params()


def build(p: Params = PARAMS) -> Part.Shape:
    disc = Part.makeCylinder(p.outer_mm / 2, p.height_mm)
    # the bore is as wide as the washer: nothing is left
    return disc.cut(Part.makeCylinder(p.outer_mm / 2, p.height_mm))
