"""Checks on a Part Studio's feature list, as codecrew recorded it from Onshape
(design/onshape/features.json): deterministic, no Onshape access needed.
One JSON object per line: file, line, code, message, severity."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

# dimensions that may stay plain numbers: zero, and the angles every design uses
PLAIN_OK = re.compile(r"^\s*(0+(\.0+)?\s*(mm|cm|m|in|deg)?|(90|180|270|360)\s*deg)\s*$")
DEFAULT_NAME = re.compile(r"^(Sketch|Extrude|Revolve|Fillet|Chamfer|Shell|Hole|Linear pattern|Circular pattern|"
                          r"Mirror|Sweep|Loft|Plane|Variable|Boolean|Split|Draft|Rib|Thicken)\s*\d+$")


def report(file: str, code: str, message: str, line: int | None = None, severity: str = "error") -> None:
    print(json.dumps({"file": file, "line": line, "code": code, "message": message, "severity": severity}))


def line_of(lines: list[str], needle: str) -> int | None:
    for n, text in enumerate(lines, 1):
        if needle in text:
            return n
    return None


def quantities(value: Any, where: str = "") -> list[tuple[str, str]]:
    """(parameter id, expression) of every quantity parameter, at any depth (sketch dimensions too)."""
    found: list[tuple[str, str]] = []
    if isinstance(value, dict):
        if "expression" in value and str(value.get("btType", "")).startswith("BTMParameterQuantity"):
            found.append((str(value.get("parameterId") or where), str(value["expression"])))
        for k, v in value.items():
            found += quantities(v, str(value.get("parameterId") or where or k))
    elif isinstance(value, list):
        for v in value:
            found += quantities(v, where)
    return found


def main() -> int:
    rel = sys.argv[1] if len(sys.argv) > 1 else "design/onshape/features.json"
    path = Path(rel)
    if not path.is_file():
        report(rel, "snapshot-missing", "No Onshape snapshot yet. codecrew writes it after each pass when the "
               "project has an Onshape document and the agent an Onshape server with the design guard.",
               severity="warning")
        return 0
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    try:
        data = json.loads(text)
    except ValueError as e:
        report(rel, "invalid-snapshot", f"Not valid JSON: {e}", 1)
        return 0
    features = data.get("features") or []
    if not features:
        report(rel, "empty", "The Part Studio has no features yet.", 1)
        return 0
    states = data.get("featureStates") or {}
    for f in features:
        fid, name, kind = str(f.get("featureId", "?")), str(f.get("name", "?")), str(f.get("featureType", "?"))
        line = line_of(lines, f'"featureId": "{fid}"')
        status = str((states.get(fid) or {}).get("featureStatus", "OK"))
        if status not in ("OK", "INFO"):
            why = (states.get(fid) or {}).get("statusMsg") or (states.get(fid) or {}).get("statusEnum") or status
            report(rel, "regeneration", f"Feature '{name}' ({kind}) fails in Onshape: {why}", line,
                   "warning" if status == "WARNING" else "error")
        if kind != "assignVariable":  # variables are where numbers belong
            for param, expr in quantities(f.get("parameters") or []) + quantities(f.get("entities") or []) + \
                    quantities(f.get("constraints") or []):
                if "#" not in expr and not PLAIN_OK.match(expr):
                    report(rel, "literal-dimension", f"'{name}': {param} is typed in as {expr!r}. Put it in a "
                           "variable (#name) and use that, so the design stays parametric.", line)
        if DEFAULT_NAME.match(name):
            report(rel, "default-name", f"'{name}' still has its default name: name it after what it does "
                   "(e.g. 'Mounting holes').", line, "warning")
    return 0


if __name__ == "__main__":
    sys.exit(main())
