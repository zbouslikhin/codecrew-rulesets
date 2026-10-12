"""A block with a slot in its side."""

from dataclasses import dataclass

import FreeCAD as App
import Part


@dataclass(frozen=True)
class Params:
    size_mm: float = 30.0
    height_mm: float = 20.0
    slot_width_mm: float = 10.0
    slot_height_mm: float = 5.0


PARAMS = Params()


def build(p: Params = PARAMS) -> Part.Shape:
    block = Part.makeBox(p.size_mm, p.size_mm, p.height_mm)
    slot = Part.makeBox(
        p.size_mm,
        p.slot_width_mm,
        p.slot_height_mm,
        App.Vector(0, (p.size_mm - p.slot_width_mm) / 2, (p.height_mm - p.slot_height_mm) / 2),
    )
    return block.cut(slot)
