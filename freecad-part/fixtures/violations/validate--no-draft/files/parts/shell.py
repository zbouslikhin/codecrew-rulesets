"""A moulded shell."""

from dataclasses import dataclass

import FreeCAD as App
import Part


@dataclass(frozen=True)
class Params:
    length_mm: float = 40.0
    width_mm: float = 30.0
    height_mm: float = 20.0
    wall_mm: float = 2.0


PARAMS = Params()


def build(p: Params = PARAMS) -> Part.Shape:
    shell = Part.makeBox(p.length_mm, p.width_mm, p.height_mm)
    core = Part.makeBox(
        p.length_mm - 2 * p.wall_mm,
        p.width_mm - 2 * p.wall_mm,
        p.height_mm,
        App.Vector(p.wall_mm, p.wall_mm, -p.wall_mm),
    )
    return shell.cut(core)
