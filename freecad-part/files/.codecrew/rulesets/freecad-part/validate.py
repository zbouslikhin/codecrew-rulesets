"""Engineering checks for FreeCAD parts: deterministic, no model involved.

Every module in parts/ is one part:
    PARAMS   an instance of a dataclass: the part's dimensions, each named with its unit
    build(p) returns the part as a Part.Shape
Optional:
    PARAM_RANGES     {"wall_mm": (1.2, 4.0)}: the range the part must build across
    DENSITY_G_CM3    for a mass estimate
Checked: the contract, units in parameter names, that it builds, a valid solid, that it
still builds when each dimension changes (±10%, or across PARAM_RANGES), STEP export, and
a test file per part. One JSON object per line: file, line, code, message, severity."""

from __future__ import annotations

import dataclasses
import importlib.util
import inspect
import json
import sys
import tempfile
import traceback
from pathlib import Path

import FreeCAD  # noqa: E402,F401  must come before Part: `import Part` alone crashes FreeCAD 1.1

UNIT_SUFFIXES = ("_mm", "_deg", "_rad", "_n", "_nm", "_kg", "_g", "_mpa", "_count", "_pct", "_ratio", "_s")
VARIATION = 0.10


def report(file: str, code: str, message: str, line: int | None = None, severity: str = "error") -> None:
    print(json.dumps({"file": file, "line": line, "code": code, "message": message, "severity": severity}))


def line_of(source: str, needle: str) -> int | None:
    for n, text in enumerate(source.splitlines(), 1):
        if needle in text:
            return n
    return None


def error_line(exc: BaseException, path: Path) -> int | None:
    for frame in reversed(traceback.extract_tb(exc.__traceback__)):
        if Path(frame.filename).resolve() == path.resolve():
            return frame.lineno
    return None


def check_shape(shape, what: str) -> str | None:
    """None when it's a usable part; otherwise why not."""
    import Part

    if not isinstance(shape, Part.Shape):
        return f"{what} returned {type(shape).__name__}, not a Part.Shape"
    if shape.isNull():
        return f"{what} returned an empty shape"
    if not shape.isValid():
        return f"{what} returned an invalid shape (self-intersecting or broken topology)"
    if not shape.Solids or shape.Volume <= 1e-9:
        return f"{what} leaves no solid material (volume {shape.Volume:.3g} mm³)"
    return None


def validate(path: Path, root: Path) -> None:
    import Part  # noqa: F401  (FreeCAD must be importable)

    rel = path.relative_to(root).as_posix()
    source = path.read_text(encoding="utf-8")
    spec = importlib.util.spec_from_file_location(f"parts_{path.stem}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as e:  # noqa: BLE001
        report(rel, "build-error", f"importing the part fails: {type(e).__name__}: {e}", error_line(e, path))
        return

    params = getattr(module, "PARAMS", None)
    build = getattr(module, "build", None)
    if params is None or not dataclasses.is_dataclass(params) or not callable(build):
        report(rel, "contract", "a part defines PARAMS (a dataclass instance with its dimensions) and "
               "build(params) returning a Part.Shape", 1)
        return

    numeric = [f for f in dataclasses.fields(params) if isinstance(getattr(params, f.name), (int, float))
               and not isinstance(getattr(params, f.name), bool)]
    for f in numeric:
        if not f.name.endswith(UNIT_SUFFIXES):
            report(rel, "param-unit", f"parameter '{f.name}' has no unit in its name: call it e.g. "
                   f"'{f.name.lower()}_mm' (units: {', '.join(s[1:] for s in UNIT_SUFFIXES)})",
                   line_of(source, f.name))

    try:
        shape = build(params)
    except Exception as e:  # noqa: BLE001
        report(rel, "build-error", f"build() fails with its own PARAMS: {type(e).__name__}: {e}", error_line(e, path))
        return
    problem = check_shape(shape, "build()")
    if problem:
        report(rel, "invalid-shape" if "invalid" in problem else "no-solid", problem, line_of(source, "def build"))
        return

    # still a part when the dimensions change: that's what makes it parametric
    ranges = getattr(module, "PARAM_RANGES", {}) or {}
    for f in (f for f in numeric if isinstance(getattr(params, f.name), float) and not f.name.endswith("_count")):
        value = getattr(params, f.name)
        tries = ranges.get(f.name) or (value * (1 - VARIATION), value * (1 + VARIATION))
        for v in tries:
            try:
                changed = build(dataclasses.replace(params, **{f.name: v}))
                why = check_shape(changed, f"with {f.name} = {v:g}")
            except Exception as e:  # noqa: BLE001
                why = f"build() fails with {f.name} = {v:g}: {type(e).__name__}: {e}"
            if why:
                span = "across PARAM_RANGES" if f.name in ranges else f"±{VARIATION:.0%}"
                report(rel, "not-parametric", f"the part breaks when {f.name} changes {span}: {why}. Make the "
                       "geometry follow the parameters (e.g. limit a fillet to the wall it rounds), or declare "
                       "the valid range in PARAM_RANGES", line_of(source, f.name))
                break

    with tempfile.TemporaryDirectory() as tmp:
        try:
            shape.exportStep(str(Path(tmp) / "part.step"))
        except Exception as e:  # noqa: BLE001
            report(rel, "export-failed", f"STEP export fails: {e}", line_of(source, "def build"))

    bb = shape.BoundBox
    info = f"{shape.Volume:,.1f} mm³, {bb.XLength:.2f} x {bb.YLength:.2f} x {bb.ZLength:.2f} mm"
    density = getattr(module, "DENSITY_G_CM3", None)
    if isinstance(density, (int, float)):
        info += f", {shape.Volume / 1000 * density:.1f} g at {density} g/cm³"
    report(rel, "summary", info, severity="info")

    if not (root / "tests" / f"test_{path.stem}.py").is_file():
        report(rel, "missing-test", f"no tests/test_{path.stem}.py: every part has a test that builds it and "
               "checks what matters (dimensions, volume, holes)", 1)


def main() -> int:
    root = Path.cwd()
    parts_dir = root / (sys.argv[1] if len(sys.argv) > 1 else "parts")
    sys.path.insert(0, str(root))
    for path in sorted(parts_dir.glob("*.py")):
        if path.name != "__init__.py":
            validate(path, root)
    return 0


if __name__ == "__main__":
    sys.exit(main())
