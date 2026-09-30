import FreeCAD  # noqa: F401
import Part


def make() -> Part.Shape:
    return Part.makeBox(10, 10, 2)
