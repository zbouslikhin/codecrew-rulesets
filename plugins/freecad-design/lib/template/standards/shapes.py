"""Standard parts as geometry, for assemblies (needs FreeCAD).

A screw is built with the underside of its head at the origin and its shank along -Z, so
placing it is: move it to the top of the hole it goes into. The shank has the thread's nominal
diameter; a tapped hole is modelled at its tap-drill diameter, and the checks allow exactly
that overlap as thread engagement.
"""

from __future__ import annotations

import FreeCAD as App  # must come before Part
import Part

from standards import fasteners


def socket_head_screw(thread: str, length_mm: float) -> Part.Shape:
    """ISO 4762: head on top (z 0 to head height), shank below (z 0 to -length)."""
    d = fasteners.diameter(thread)
    head = Part.makeCylinder(fasteners.head_diameter(thread) / 2, fasteners.head_height(thread))
    shank = Part.makeCylinder(d / 2, length_mm, App.Vector(0, 0, -length_mm))
    return head.fuse(shank).removeSplitter()


def from_designation(designation: str) -> Part.Shape:
    """The geometry of a standard part by its designation, e.g. "ISO 4762 M4x12"."""
    part = fasteners.parse(designation)
    if part is None or part.kind != "screw" or part.length_mm is None:
        raise ValueError(
            f"no geometry for '{designation}': screws (ISO 4762 M<d>x<length>) are modelled"
        )
    return socket_head_screw(part.thread, part.length_mm)


def placed_screw(designation: str, seat, toward) -> Part.Shape:
    """A screw in place: the underside of its head on `seat` (the point on the face the head bears
    on), its shank pointing `toward` (into the parts it holds). Both are FreeCAD vectors or
    (x, y, z) tuples. The head is on the side `toward` points away from, so name the direction
    the screw goes in, not the one it comes from:

        placed_screw("ISO 4762 M3x12", seat=(x_inner_face, y, z), toward=(1, 0, 0))

    puts the head against a face at x_inner_face and the shank through the material towards +x.
    """
    seat = App.Vector(*seat) if not isinstance(seat, App.Vector) else App.Vector(seat)
    toward = App.Vector(*toward) if not isinstance(toward, App.Vector) else App.Vector(toward)
    if toward.Length < 1e-9:
        raise ValueError("toward must be a direction, not zero")
    toward.normalize()
    screw = from_designation(designation)
    screw.Placement = App.Placement(seat, App.Rotation(App.Vector(0, 0, -1), toward))
    return screw
