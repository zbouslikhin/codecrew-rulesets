"""The plate screwed onto the block with one M3x12."""

import FreeCAD as App
import Part

from parts import block, plate
from standards import shapes

B, P = block.PARAMS, plate.PARAMS


def build() -> dict[str, Part.Shape]:
    lower = block.build(B)
    upper = plate.build(P)
    upper.translate(App.Vector(0, 0, B.height_mm))
    top = B.height_mm + P.thickness_mm
    screw = shapes.placed_screw(
        "ISO 4762 M3x12", App.Vector(P.width_mm / 2, P.depth_mm / 2, top), App.Vector(0, 0, -1)
    )
    return {"block": lower, "plate": upper, "standard:ISO 4762 M3x12:1": screw}
