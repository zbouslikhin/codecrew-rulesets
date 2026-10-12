"""A moulded cap: an open shell with drafted walls of even thickness."""

from dataclasses import dataclass

import FreeCAD as App
import Part


@dataclass(frozen=True)
class Params:
    length_mm: float = 40.0
    width_mm: float = 30.0
    height_mm: float = 20.0
    wall_mm: float = 2.0
    draft_deg: float = 2.0


PARAMS = Params()


def build(p: Params = PARAMS) -> Part.Shape:
    import math

    lean = p.height_mm * math.tan(math.radians(p.draft_deg))

    def tapered(length: float, width: float, height: float, at: float) -> Part.Shape:
        top = lean * height / p.height_mm
        low = [(at, at), (at + length, at), (at + length, at + width), (at, at + width)]
        high = [
            (at + top, at + top),
            (at + length - top, at + top),
            (at + length - top, at + width - top),
            (at + top, at + width - top),
        ]
        wires = [
            Part.makePolygon([App.Vector(x, y, z) for x, y in [*ring, ring[0]]])
            for ring, z in ((low, 0.0), (high, height))
        ]
        return Part.makeLoft(wires, True)

    outer = tapered(p.length_mm, p.width_mm, p.height_mm, 0.0)
    core = tapered(
        p.length_mm - 2 * p.wall_mm, p.width_mm - 2 * p.wall_mm, p.height_mm - p.wall_mm, p.wall_mm
    )
    return outer.cut(core)
