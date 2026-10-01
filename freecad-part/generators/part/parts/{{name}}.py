"""{{name_title}}: TODO what it does and what it mates with.

Material: PETG, printed (FDM, 0.4 mm nozzle). All lengths in mm.
Design intent:
- TODO the function-critical dimensions and why they are what they are;
- TODO how it's loaded, and what that means for walls, fillets and print orientation.
"""

from dataclasses import dataclass

import FreeCAD as App  # noqa: F401  (FreeCAD before Part: `import Part` alone crashes FreeCAD 1.1)
import Part

DENSITY_G_CM3 = 1.27  # PETG


@dataclass(frozen=True)
class Params:
    length_mm: float = 40.0
    width_mm: float = 20.0
    height_mm: float = 10.0


PARAMS = Params()


def build(p: Params = PARAMS) -> Part.Shape:
    """TODO the real geometry: primitives and booleans, every dimension from p."""
    return Part.makeBox(p.length_mm, p.width_mm, p.height_mm)
