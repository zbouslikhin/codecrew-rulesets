"""A milled block with a deep pocket."""

from dataclasses import dataclass

import FreeCAD as App
import Part


@dataclass(frozen=True)
class Params:
    length_mm: float = 60.0
    width_mm: float = 40.0
    height_mm: float = 40.0
    pocket_depth_mm: float = 30.0
    wall_mm: float = 8.0
    corner_radius_mm: float = 2.0


PARAMS = Params()


def build(p: Params = PARAMS) -> Part.Shape:
    block = Part.makeBox(p.length_mm, p.width_mm, p.height_mm)
    pocket = Part.makeBox(
        p.length_mm - 2 * p.wall_mm,
        p.width_mm - 2 * p.wall_mm,
        p.pocket_depth_mm,
        App.Vector(p.wall_mm, p.wall_mm, p.height_mm - p.pocket_depth_mm),
    )
    upright = [e for e in pocket.Edges if abs(e.BoundBox.ZLength - p.pocket_depth_mm) < 1e-6]
    pocket = pocket.makeFillet(p.corner_radius_mm, upright)
    return block.cut(pocket)
