from dataclasses import dataclass

import FreeCAD as App  # noqa: F401
import Part


@dataclass(frozen=True)
class Params:
    length_mm: float = 20.0
    width_mm: float = 3.0
    height_mm: float = 10.0
    radius_mm: float = 1.4


PARAMS = Params()


def build(p: Params = PARAMS) -> Part.Shape:
    bar = Part.makeBox(p.length_mm, p.width_mm, p.height_mm)
    # both long top edges rounded: two radii must fit in the width, nothing checks that
    edges = [e for e in bar.Edges if abs(e.BoundBox.ZMin - p.height_mm) < 1e-6 and e.BoundBox.XLength > 1]
    return bar.makeFillet(p.radius_mm, edges)
