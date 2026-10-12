"""A hollow float."""

from dataclasses import dataclass

import FreeCAD as App
import Part


@dataclass(frozen=True)
class Params:
    size_mm: float = 20.0
    cavity_mm: float = 10.0


PARAMS = Params()


def build(p: Params = PARAMS) -> Part.Shape:
    at = (p.size_mm - p.cavity_mm) / 2
    return Part.makeBox(p.size_mm, p.size_mm, p.size_mm).cut(
        Part.makeBox(p.cavity_mm, p.cavity_mm, p.cavity_mm, App.Vector(at, at, at))
    )
