"""A printed front panel whose four corners each got a different radius."""

from dataclasses import dataclass

import FreeCAD as App  # noqa: F401
import Part


@dataclass(frozen=True)
class Params:
    length_mm: float = 60.0
    width_mm: float = 40.0
    thickness_mm: float = 4.0
    first_radius_mm: float = 2.0
    radius_step_mm: float = 1.0


PARAMS = Params()


def build(p: Params = PARAMS) -> Part.Shape:
    panel = Part.makeBox(p.length_mm, p.width_mm, p.thickness_mm)
    corners = [(0.0, 0.0), (p.length_mm, 0.0), (p.length_mm, p.width_mm), (0.0, p.width_mm)]
    for n, (x, y) in enumerate(corners):
        upright = [
            e
            for e in panel.Edges
            if abs(e.BoundBox.ZLength - p.thickness_mm) < 1e-6
            and abs(e.BoundBox.XMin - x) < 1e-6
            and abs(e.BoundBox.XMax - x) < 1e-6
            and abs(e.BoundBox.YMin - y) < 1e-6
            and abs(e.BoundBox.YMax - y) < 1e-6
        ]
        panel = panel.makeFillet(p.first_radius_mm + n * p.radius_step_mm, upright)
    return panel
