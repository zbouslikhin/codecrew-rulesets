"""Exports parts to exports/<part>.step and .stl (for printing or CAM).

    python -B scripts/export.py               every part in parts/
    python -B scripts/export.py test_pieces   every test piece, into exports/test_pieces/
"""

import importlib
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))
folder = sys.argv[1] if len(sys.argv) > 1 else "parts"
out = root / "exports" / ("" if folder == "parts" else folder)
out.mkdir(parents=True, exist_ok=True)
total = 0.0
for path in sorted((root / folder).glob("*.py")):
    if path.name == "__init__.py":
        continue
    module = importlib.import_module(f"{folder}.{path.stem}")
    shape = module.build(module.PARAMS)
    shape.exportStep(str(out / f"{path.stem}.step"))
    shape.exportStl(str(out / f"{path.stem}.stl"))
    total += shape.Volume
    grams = shape.Volume / 1000 * 1.27
    print(f"exported {path.stem}: {shape.Volume:,.1f} mm³ ({grams:,.0f} g of PETG if solid)")
print(f"total: {total / 1000:,.0f} cm³")
