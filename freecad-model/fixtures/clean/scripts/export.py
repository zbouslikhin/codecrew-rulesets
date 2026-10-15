"""Exports every part to exports/<part>.step and .stl (for printing or CAM)."""

import importlib
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))
out = root / "exports"
out.mkdir(exist_ok=True)
for path in sorted((root / "parts").glob("*.py")):
    if path.name == "__init__.py":
        continue
    module = importlib.import_module(f"parts.{path.stem}")
    shape = module.build(module.PARAMS)
    shape.exportStep(str(out / f"{path.stem}.step"))
    shape.exportStl(str(out / f"{path.stem}.stl"))
    print(f"exported {path.stem}: {shape.Volume:,.1f} mm³")
