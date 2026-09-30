"""Mounting bracket: an L-bracket that holds a sensor on a frame.

Material: PETG, printed (FDM, 0.4 mm nozzle). All lengths in mm.
Design intent:
- two M4 clearance holes in the base, centred on its free part;
- a fillet in the inner corner, against the stress concentration there;
- walls of at least 2 mm, so the print is solid.
"""

from dataclasses import dataclass

import FreeCAD as App
import Part

DENSITY_G_CM3 = 1.27  # PETG

EPS = 1e-6


@dataclass(frozen=True)
class Params:
    width_mm: float = 40.0
    depth_mm: float = 30.0
    height_mm: float = 35.0
    thickness_mm: float = 3.0
    hole_diameter_mm: float = 4.5  # M4 clearance, medium fit
    hole_edge_distance_mm: float = 8.0
    fillet_radius_mm: float = 4.0


PARAMS = Params()


def hole_y(p: Params) -> float:
    """The holes sit centred on the part of the base in front of the wall."""
    return (p.thickness_mm + p.depth_mm) / 2


def inner_corner(shape: Part.Shape, p: Params) -> Part.Edge:
    """The edge where base and wall meet on the inside, found by where it is, not by its
    index: edge numbers change whenever the geometry does (FreeCAD's topological naming)."""
    for edge in shape.Edges:
        bb = edge.BoundBox
        if (
            abs(bb.YMin - p.thickness_mm) < EPS
            and abs(bb.YMax - p.thickness_mm) < EPS
            and abs(bb.ZMin - p.thickness_mm) < EPS
            and abs(bb.ZMax - p.thickness_mm) < EPS
            and abs(bb.XLength - p.width_mm) < EPS
        ):
            return edge
    raise ValueError("inner corner edge not found")


def build(p: Params = PARAMS) -> Part.Shape:
    base = Part.makeBox(p.width_mm, p.depth_mm, p.thickness_mm)
    wall = Part.makeBox(p.width_mm, p.thickness_mm, p.height_mm)
    bracket = base.fuse(wall).removeSplitter()

    # the fillet may not reach the holes or run past the wall: it follows the parameters
    room = hole_y(p) - p.hole_diameter_mm / 2 - p.thickness_mm
    radius = min(p.fillet_radius_mm, 0.8 * room, 0.8 * (p.height_mm - p.thickness_mm))
    bracket = bracket.makeFillet(radius, [inner_corner(bracket, p)])

    for x in (p.hole_edge_distance_mm, p.width_mm - p.hole_edge_distance_mm):
        hole = Part.makeCylinder(
            p.hole_diameter_mm / 2, 3 * p.thickness_mm, App.Vector(x, hole_y(p), -p.thickness_mm)
        )
        bracket = bracket.cut(hole)
    return bracket
