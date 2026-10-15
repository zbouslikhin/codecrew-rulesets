"""A block with a tapped M3 hole: what the screw holds in."""

from dataclasses import dataclass

import FreeCAD as App
import Part

from standards import fasteners

PRINTED = False  # machined aluminium


@dataclass(frozen=True)
class Params:
    width_mm: float = 40.0
    depth_mm: float = 30.0
    height_mm: float = 12.0
    tap_mm: float = fasteners.tap_drill("M3")
    tap_depth_mm: float = 9.0


PARAMS = Params()


def build(p: Params = PARAMS) -> Part.Shape:
    block = Part.makeBox(p.width_mm, p.depth_mm, p.height_mm)
    tap = Part.makeCylinder(
        p.tap_mm / 2,
        p.tap_depth_mm + 1,
        App.Vector(p.width_mm / 2, p.depth_mm / 2, p.height_mm - p.tap_depth_mm),
    )
    return block.cut(tap).removeSplitter()
