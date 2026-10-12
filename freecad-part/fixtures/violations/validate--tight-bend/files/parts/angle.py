"""A folded angle."""

from dataclasses import dataclass

import FreeCAD as App
import Part


@dataclass(frozen=True)
class Params:
    length_mm: float = 40.0
    width_mm: float = 20.0
    leg_mm: float = 30.0
    thickness_mm: float = 2.0


PARAMS = Params()


def build(p: Params = PARAMS) -> Part.Shape:
    base = Part.makeBox(p.length_mm, p.width_mm, p.thickness_mm)
    return base.fuse(Part.makeBox(p.thickness_mm, p.width_mm, p.leg_mm)).removeSplitter()
