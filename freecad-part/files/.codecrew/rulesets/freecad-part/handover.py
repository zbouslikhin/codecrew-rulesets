"""Hand-over to Onshape: the part proven here, rebuilt there, and kept the same.

FreeCAD is where a design is proven; Onshape is where it's used and where people change its
dimensions. design/handover.toml names the part that goes to the project's Part Studio:

    part = "mounting_bracket"

codecrew records what the Part Studio holds after each pass (design/onshape/features.json:
its features and variables; properties.json: volume, mass and bounding box as Onshape
measures them). This script compares that record with the part here.

    python handover.py            check: one JSON object per line (file, line, code, message, severity)
    python handover.py --accept   record the Onshape features as the accepted hand-over
    python handover.py --pull     take variable values changed in Onshape into the part's Params

Checked: every dimension of Params is an Onshape variable of the same name and value; the two
solids have the same volume and size; and, once a hand-over is accepted, the features in
Onshape are the accepted ones (anything else is drift: only variables may change there).
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
import tomllib
from pathlib import Path

HERE = Path(__file__).resolve().parent
SNAPSHOT = "design/onshape/features.json"
PROPERTIES = "design/onshape/properties.json"
LOCK = "design/onshape/handover.lock.json"
CONFIG = "design/handover.toml"
VOLUME_TOLERANCE = 0.001  # the two solids' volumes agree to a tenth of a percent
SIZE_TOLERANCE_MM = 0.01
UNITS = {"mm": 1.0, "cm": 10.0, "m": 1000.0, "in": 25.4, "deg": 1.0, "": 1.0}
LITERAL = re.compile(r"^\s*(-?\d+(?:\.\d+)?)\s*\*?\s*(mm|cm|m|in|deg)?\s*$")


def report(file: str, code: str, message: str, line: int | None = 1, severity: str = "error") -> None:
    print(json.dumps({"file": file, "line": line, "code": code, "message": message, "severity": severity}))


def variable_name(parameter: str) -> tuple[str, str]:
    """A Params field as an Onshape variable: (its name without the unit, the unit)."""
    for suffix, unit in (("_mm", "mm"), ("_deg", "deg")):
        if parameter.endswith(suffix):
            return parameter.removesuffix(suffix), unit
    return parameter, ""


def expected(root: Path, part: str) -> dict:
    """What Onshape must hold for this part: its variables, and its solid's volume and size."""
    sys.path.insert(0, str(root))
    sys.path.insert(0, str(HERE))
    import validate as v

    path = root / "parts" / f"{part}.py"
    spec = importlib.util.spec_from_file_location(f"handover_{part}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    params = module.PARAMS
    shape = module.build(params)
    box = v.extent(shape)
    variables = {}
    for field in params.__dataclass_fields__:
        value = getattr(params, field)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            name, unit = variable_name(field)
            variables[name] = {"value": float(value), "unit": unit, "parameter": field}
    return {
        "part": part,
        "variables": variables,
        "volume_mm3": shape.Volume,
        "bounding_box_mm": sorted((box.XLength, box.YLength, box.ZLength)),
    }


def recorded(root: Path) -> tuple[dict[str, str], list[dict]] | None:
    """What Onshape holds: (variable name -> its expression, the other features in order)."""
    try:
        data = json.loads((root / SNAPSHOT).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    variables: dict[str, str] = {}
    features: list[dict] = []
    for f in data.get("features") or []:
        params = f.get("parameters") or []
        if f.get("featureType") == "assignVariable":
            name = next((p.get("value") for p in params if p.get("parameterId") == "name"), None)
            value = next((p.get("expression") for p in params if str(p.get("parameterId", "")).endswith("Value") and p.get("expression")), None)
            if isinstance(name, str):
                variables[name] = str(value or "")
            continue
        features.append(
            {
                "id": str(f.get("featureId") or ""),
                "type": str(f.get("featureType") or f.get("btType") or ""),
                "name": str(f.get("name") or ""),
                "expressions": sorted(expressions(f)),
            }
        )
    return variables, features


def expressions(value: object) -> list[str]:
    """Every dimension expression in a feature, at any depth: a change to one is a change."""
    found: list[str] = []
    if isinstance(value, dict):
        if "expression" in value and str(value.get("btType", "")).startswith("BTMParameterQuantity"):
            found.append(f"{value.get('parameterId', '')}={value['expression']}")
        for item in value.values():
            found += expressions(item)
    elif isinstance(value, list):
        for item in value:
            found += expressions(item)
    return found


def literal(expression: str, unit: str) -> float | None:
    """A variable's value as a number in the part's unit; None when it's an expression."""
    found = LITERAL.match(expression)
    if not found or (found.group(2) or "") not in UNITS:
        return None
    given = found.group(2) or ""
    if unit == "deg" or given == "deg":
        return float(found.group(1)) if given in ("deg", "") and unit in ("deg", "") else None
    return float(found.group(1)) * UNITS[given]


def configured(root: Path) -> str | None:
    try:
        part = tomllib.loads((root / CONFIG).read_text(encoding="utf-8")).get("part")
    except (OSError, tomllib.TOMLDecodeError):
        return None
    return part if isinstance(part, str) and (root / "parts" / f"{part}.py").is_file() else None


def check(root: Path, quiet: bool = False) -> int:
    """Returns the number of errors."""
    errors = 0

    def say(file: str, code: str, message: str, severity: str = "error") -> None:
        nonlocal errors
        errors += severity == "error"
        if not quiet:
            report(file, code, message, 1, severity)

    if not (root / CONFIG).is_file():
        return 0
    part = configured(root)
    if part is None:
        say(CONFIG, "handover-invalid", 'design/handover.toml names the part that goes to Onshape: part = "<name>", a part in parts/')
        return errors
    held = recorded(root)
    if held is None:
        say(CONFIG, "handover-not-recorded", "nothing is recorded from Onshape yet (design/onshape/features.json): "
            "codecrew writes it after a pass of an agent with the Onshape server", "warning")
        return errors
    variables, features = held
    try:
        want = expected(root, part)
    except Exception as e:  # noqa: BLE001  (the part's own check reports why)
        say(f"parts/{part}.py", "handover-unverified", f"the part doesn't build here, so it can't be compared: {e}")
        return errors

    for name, v in want["variables"].items():
        said = f"{v['value']:g} {v['unit']}".strip()
        if name not in variables:
            say(SNAPSHOT, "variable-missing", f"Onshape has no variable #{name}: the part's {v['parameter']} is {said}. "
                "Every dimension of Params is a variable there, with the same name without its unit")
            continue
        value = literal(variables[name], v["unit"])
        if value is None:
            say(SNAPSHOT, "variable-not-literal", f"#{name} is '{variables[name]}' in Onshape: a handed-over variable "
                f"holds a plain value ({said}), so it can be changed there and taken back here")
        elif abs(value - v["value"]) > 1e-6:
            say(SNAPSHOT, "variable-differs", f"#{name} is {value:g} {v['unit']} in Onshape and {said} here "
                f"({v['parameter']}): they must agree. Changed in Onshape on purpose? Run the sync pipeline to take it back")

    try:
        measured = json.loads((root / PROPERTIES).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        measured = {}
    volume = measured.get("volume_mm3")
    if not isinstance(volume, (int, float)):
        say(PROPERTIES, "handover-unverified", "Onshape's measurements aren't recorded (design/onshape/properties.json), "
            "so nothing shows that the solid there is the one proven here")
    else:
        if abs(volume - want["volume_mm3"]) > VOLUME_TOLERANCE * want["volume_mm3"]:
            say(PROPERTIES, "volume-differs", f"the solid in Onshape has {volume:,.1f} mm³, the part here {want['volume_mm3']:,.1f} mm³ "
                f"({(volume / want['volume_mm3'] - 1) * 100:+.2f}%): they aren't the same shape. Compare the features with the part's build()")
        box = measured.get("bounding_box_mm")
        if isinstance(box, list) and len(box) == 3:
            there, here = sorted(float(b) for b in box), want["bounding_box_mm"]
            if any(abs(a - b) > SIZE_TOLERANCE_MM for a, b in zip(there, here, strict=True)):
                say(PROPERTIES, "size-differs", "the solid in Onshape measures " + " x ".join(f"{b:.2f}" for b in there)
                    + " mm, the part here " + " x ".join(f"{b:.2f}" for b in here) + " mm")

    try:
        lock = json.loads((root / LOCK).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        lock = None
    if lock is not None:
        before = {f["id"]: f for f in lock.get("features", [])}
        now = {f["id"]: f for f in features}
        changes = [f"added: {f['name']} ({f['type']})" for i, f in now.items() if i not in before]
        changes += [f"removed: {f['name']} ({f['type']})" for i, f in before.items() if i not in now]
        changes += [f"changed: {f['name']} ({f['type']})" for i, f in now.items() if i in before and f != before[i]]
        if not changes and list(now) != list(before):
            changes.append("the order of the features changed")
        if changes:
            say(SNAPSHOT, "drift", "the features in Onshape aren't the accepted ones any more (" + "; ".join(changes[:8])
                + "). Only variable values may change there: make the change in the part here and hand it over again")
    return errors


def accept(root: Path) -> int:
    if check(root, quiet=True):
        check(root)
        print("not accepted: the Onshape part doesn't match the part here yet", file=sys.stderr)
        return 1
    held, part = recorded(root), configured(root)
    if held is None or part is None:
        print("not accepted: nothing is recorded from Onshape, or design/handover.toml names no part", file=sys.stderr)
        return 1
    variables, features = held
    lock = {"part": part, "variables": sorted(variables), "features": features}
    (root / LOCK).write_text(json.dumps(lock, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"accepted: {len(features)} feature(s) and {len(variables)} variable(s) of {part}")
    return 0


def pull(root: Path) -> int:
    """Variable values changed in Onshape, written into the part's Params. Only after a
    hand-over was accepted; the checks that follow then judge the changed part."""
    part, held = configured(root), recorded(root)
    if part is None or held is None or not (root / LOCK).is_file():
        return 0
    variables, _ = held
    path = root / "parts" / f"{part}.py"
    source = path.read_text(encoding="utf-8")
    changed = []
    for name, v in expected(root, part)["variables"].items():
        value = literal(variables.get(name, ""), v["unit"])
        if value is None or abs(value - v["value"]) <= 1e-6:
            continue
        field = re.compile(rf"^(\s+{re.escape(v['parameter'])}\s*:\s*\w+\s*=\s*)([^#\n]+?)(\s*(#.*)?)$", re.MULTILINE)
        new, count = field.subn(lambda m, value=value: f"{m.group(1)}{value!r}{m.group(3)}", source, count=1)
        if count:
            source = new
            changed.append(f"{v['parameter']}: {v['value']:g} -> {value:g}")
    if changed:
        path.write_text(source, encoding="utf-8")
        print(f"taken from Onshape into parts/{part}.py: " + "; ".join(changed))
    return 0


def main() -> int:
    root = Path.cwd()
    if "--accept" in sys.argv:
        return accept(root)
    if "--pull" in sys.argv:
        return pull(root)
    check(root)
    return 0


if __name__ == "__main__":
    sys.exit(main())
