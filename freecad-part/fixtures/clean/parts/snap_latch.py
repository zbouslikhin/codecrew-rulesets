"""Snap latch: a block with a snap arm that hooks behind the edge of a housing window.

Material: PETG, printed (FDM) lying on its side: the profile below is the first layer, so the
arm bends along its layers, not across them. All lengths in mm.
Design intent:
- the arm is long and thin enough to stay well inside PETG's permissible strain when the hook
  is pushed aside by its own depth (the spec's load L1);
- the hook has a ramp to snap in and a square face to hold.
"""

from dataclasses import dataclass

import FreeCAD as App
import Part


@dataclass(frozen=True)
class Params:
    base_length_mm: float = 20.0
    base_height_mm: float = 6.0
    width_mm: float = 8.0
    arm_length_mm: float = 20.0
    arm_thickness_mm: float = 1.6
    hook_depth_mm: float = 1.2  # how far the arm is pushed aside to snap in
    hook_land_mm: float = 0.8
    hook_ramp_mm: float = 3.0


PARAMS = Params()


def profile(p: Params) -> list[tuple[float, float]]:
    """The outline, seen along the print direction: the base, the arm rising from its left
    end, the hook at the arm's tip pointing right."""
    t = p.arm_thickness_mm
    root = p.base_height_mm
    tip = root + p.arm_length_mm
    return [
        (0.0, 0.0),
        (p.base_length_mm, 0.0),
        (p.base_length_mm, root),
        (t, root),
        (t, tip),
        (t + p.hook_depth_mm, tip),
        (t + p.hook_depth_mm, tip + p.hook_land_mm),
        (t, tip + p.hook_land_mm + p.hook_ramp_mm),
        (0.0, tip + p.hook_land_mm + p.hook_ramp_mm),
    ]


def build(p: Params = PARAMS) -> Part.Shape:
    points = [App.Vector(x, y, 0.0) for x, y in profile(p)]
    face = Part.Face(Part.makePolygon([*points, points[0]]))
    return face.extrude(App.Vector(0.0, 0.0, p.width_mm))
