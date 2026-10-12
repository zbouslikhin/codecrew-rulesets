"""Spacer: a plain block between two plates. Material: PETG, printed."""

from dataclasses import dataclass

import FreeCAD as App  # noqa: F401
import Part

DENSITY_G_CM3 = 1.27


@dataclass(frozen=True)
class Params:
    length_mm: float = 20.0
    width_mm: float = 10.0
    height_mm: float = 5.0


PARAMS = Params()


def build(p: Params = PARAMS) -> Part.Shape:
    return Part.makeBox(p.length_mm, p.width_mm, p.height_mm)
