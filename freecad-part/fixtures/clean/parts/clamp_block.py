"""A milled clamp block: a pocket with radiused corners and two through holes."""

from dataclasses import dataclass

import FreeCAD as App
import Part


@dataclass(frozen=True)
class Params:
    length_mm: float = 60.0
    width_mm: float = 40.0
    height_mm: float = 16.0
    pocket_depth_mm: float = 8.0
    corner_radius_mm: float = 3.0
    hole_diameter_mm: float = 4.5
    wall_mm: float = 8.0


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
    block = block.cut(pocket.makeFillet(p.corner_radius_mm, upright))
    for x in (p.wall_mm / 2, p.length_mm - p.wall_mm / 2):
        hole = Part.makeCylinder(
            p.hole_diameter_mm / 2, p.height_mm + 2, App.Vector(x, p.width_mm / 2, -1)
        )
        block = block.cut(hole)
    return block.removeSplitter()
