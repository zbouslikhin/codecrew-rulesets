"""A turned tool handle: a round bar a hand closes around, its ends rounded."""

from dataclasses import dataclass

import FreeCAD as App  # noqa: F401
import Part


@dataclass(frozen=True)
class Params:
    diameter_mm: float = 35.0
    length_mm: float = 110.0
    end_radius_mm: float = 4.0


PARAMS = Params()


def build(p: Params = PARAMS) -> Part.Shape:
    bar = Part.makeCylinder(p.diameter_mm / 2, p.length_mm)
    return bar
