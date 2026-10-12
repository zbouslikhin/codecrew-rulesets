"""A printed table on one leg."""

from dataclasses import dataclass

import FreeCAD as App
import Part


@dataclass(frozen=True)
class Params:
    top_mm: float = 40.0
    thickness_mm: float = 3.0
    leg_mm: float = 6.0
    leg_height_mm: float = 20.0


PARAMS = Params()


def build(p: Params = PARAMS) -> Part.Shape:
    top = Part.makeBox(p.top_mm, p.top_mm, p.thickness_mm, App.Vector(0, 0, p.leg_height_mm))
    at = (p.top_mm - p.leg_mm) / 2
    return top.fuse(
        Part.makeBox(p.leg_mm, p.leg_mm, p.leg_height_mm, App.Vector(at, at, 0))
    ).removeSplitter()
