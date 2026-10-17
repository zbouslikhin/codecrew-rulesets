"""Exports parts to exports/<part>.step (as modelled, for CAD) and exports/<part>.stl (for
printing: turned so the face it prints on, RESTS_ON, lies on the bed at z 0). Bought parts
(PRINTED = False) get a STEP only.

python -B scripts/export.py               every part in parts/
python -B scripts/export.py test_pieces   every test piece, into exports/test_pieces/
"""

import importlib
import sys
from pathlib import Path

import FreeCAD as App
import Mesh
import MeshPart

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))
folder = sys.argv[1] if len(sys.argv) > 1 else "parts"
out = root / "exports" / ("" if folder == "parts" else folder)
out.mkdir(parents=True, exist_ok=True)

# the rotation that puts each face down (onto -z)
DOWN = {
    "-z": None,
    "+z": (App.Vector(1, 0, 0), 180),
    "-y": (App.Vector(1, 0, 0), 90),
    "+y": (App.Vector(1, 0, 0), -90),
    "-x": (App.Vector(0, 1, 0), -90),
    "+x": (App.Vector(0, 1, 0), 90),
}


def for_printing(shape, rests_on: str):
    s = shape.copy()
    turn = DOWN[rests_on]
    if turn:
        s.rotate(App.Vector(0, 0, 0), *turn)
    bb = s.BoundBox
    s.translate(App.Vector(-bb.XMin, -bb.YMin, -bb.ZMin))
    return s


total = 0.0
for path in sorted((root / folder).glob("*.py")):
    if path.name == "__init__.py":
        continue
    module = importlib.import_module(f"{folder}.{path.stem}")
    shape = module.build(module.PARAMS)
    shape.exportStep(str(out / f"{path.stem}.step"))
    if not getattr(module, "PRINTED", True):
        print(f"exported {path.stem}: STEP only (bought, not printed)")
        continue
    flat = for_printing(shape, getattr(module, "RESTS_ON", "-z"))
    mesh = MeshPart.meshFromShape(Shape=flat, LinearDeflection=0.02, AngularDeflection=0.2)
    Mesh.Mesh(mesh).write(str(out / f"{path.stem}.stl"))
    total += shape.Volume
    bb = flat.BoundBox
    print(
        f"exported {path.stem}: {bb.XLength:.0f} x {bb.YLength:.0f} x {bb.ZLength:.0f} mm "
        f"on the bed, {shape.Volume / 1000 * 1.27:,.0f} g of PETG if solid"
    )
print(f"total printed: {total / 1000:,.0f} cm³")
