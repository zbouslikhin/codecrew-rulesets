"""A block."""

from dataclasses import dataclass

import FreeCAD as App
import Part


@dataclass(frozen=True)
class Params:
    length_mm: float = 40.0
    width_mm: float = 30.0
    height_mm: float = 10.0


PARAMS = Params()


def build(p: Params = PARAMS) -> Part.Shape:
    return Part.makeBox(p.length_mm, p.width_mm, p.height_mm)
