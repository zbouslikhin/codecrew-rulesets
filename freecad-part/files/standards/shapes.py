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
