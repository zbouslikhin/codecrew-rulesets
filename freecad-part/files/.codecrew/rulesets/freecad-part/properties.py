"""What Onshape measures on the Part Studio, in mm, mm³ and g: the `properties` recorder's
transform. codecrew calls Onshape (mass properties, bounding box) and gives this script the
results in a file, {"mass": ..., "box": ...} (null for a call that failed); what it prints is
written to design/onshape/properties.json. Nothing printed: nothing measured, nothing written.

    python -B properties.py <input.json>
"""

from __future__ import annotations

import json
import sys
from typing import Any


def first(value: Any) -> float | None:
    """Onshape gives [value, least, most]."""
    value = value[0] if isinstance(value, list) and value else value
    return float(value) if isinstance(value, (int, float)) else None


def properties(data: dict[str, Any]) -> dict[str, Any]:
    """Onshape's mass properties or bounding box (SI units) as mm³, g and mm."""
    out: dict[str, Any] = {}
    bodies = data.get("bodies")
    if isinstance(bodies, dict) and bodies:
        whole = bodies.get("-all-") or next(iter(bodies.values()))
        if isinstance(whole, dict):
            volume = first(whole.get("volume"))
            if volume is not None:
                out["volume_mm3"] = round(volume * 1e9, 4)
            mass = first(whole.get("mass"))
            if mass is not None and whole.get("hasMass", True):  # no material: no mass to compare
                out["mass_g"] = round(mass * 1000, 4)
    if all(isinstance(data.get(k), (int, float)) for k in ("lowX", "lowY", "lowZ", "highX", "highY", "highZ")):
        out["bounding_box_mm"] = [round((data[f"high{a}"] - data[f"low{a}"]) * 1000, 4) for a in ("X", "Y", "Z")]
    return out


def main(path: str) -> None:
    with open(path, encoding="utf-8") as f:
        results = json.load(f)
    measured: dict[str, Any] = {}
    for data in results.values():
        if isinstance(data, dict):
            measured.update(properties(data))
    if measured:
        print(json.dumps(measured, indent=2, sort_keys=True))


if __name__ == "__main__":
    main(sys.argv[1])
