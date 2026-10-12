"""A long printed rail."""

from dataclasses import dataclass

import FreeCAD as App
import Part


@dataclass(frozen=True)
class Params:
    length_mm: float = 300.0
    width_mm: float = 20.0
    height_mm: float = 10.0


PARAMS = Params()


def build(p: Params = PARAMS) -> Part.Shape:
    return Part.makeBox(p.length_mm, p.width_mm, p.height_mm)
