"""The checks of freecad-model: errors only for what is objectively wrong, warnings for the rest.

    python -B .codecrew/rulesets/freecad-model/check.py

Errors (they stop a step):
- build-error, contract, invalid-shape: a part or assembly doesn't build into valid solids
- too-large: a printed part doesn't fit the printer's bed (design/printer.toml), in any orientation
- overlap: two components of an assembly occupy the same space
- thread-engagement: a screw in a tapped hole has too little thread in it
Warnings (shown to you, never sent back to the agent as failures):
- sharp-edge, overhang, thin-wall, small-hole: what printing and a hand would notice
- screw-holds-nothing: a screw that reaches only one part
- no-printer: there is no design/printer.toml, so nothing is checked against a bed

One JSON object per line: file, line, code, message, severity.
"""

from __future__ import annotations

import json
import sys
import tomllib
from pathlib import Path

import FreeCAD  # noqa: F401  must come before Part

sys.path.insert(0, str(Path(__file__).resolve().parent))
import appearance  # noqa: E402
import dfm  # noqa: E402
from model import Component, LoadError, load, overlaps, screw_of  # noqa: E402

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT))
try:
    from standards import fasteners  # noqa: E402
except ImportError:  # a project without the standards library
    fasteners = None

OVERLAP_MM3 = 1e-3
NEAR_MM = 1.0  # a screw within this of a part reaches it (an insert's hole is a little wider)


def report(file: str, code: str, message: str, severity: str = "error", line: int | None = None) -> None:
    print(json.dumps({"file": file, "line": line, "code": code, "message": message, "severity": severity}))


def line_of(path: Path, needle: str) -> int | None:
    try:
        for n, text in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if needle in text:
                return n
    except OSError:
        pass
    return None


def printer_bed(root: Path) -> list[float] | None:
    path = root / "design" / "printer.toml"
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return None
    bed = data.get("bed_mm")
    if isinstance(bed, list) and len(bed) == 3 and all(isinstance(v, (int, float)) and v > 0 for v in bed):
        return [float(v) for v in bed]
    return None


def module_flag(path: Path, name: str, default):
    """A module-level constant, read from the source without running it again."""
    for text in path.read_text(encoding="utf-8").splitlines():
        stripped = text.strip()
        if stripped.startswith(f"{name} =") or stripped.startswith(f"{name}:"):
            value = stripped.split("=", 1)[-1].split("#")[0].strip()
            try:
                return json.loads(value.replace("True", "true").replace("False", "false").replace("'", '"'))
            except ValueError:
                return default
    return default


def valid(rel: str, path: Path, components: list[Component]) -> bool:
    ok = True
    for c in components:
        what = f"component '{c.name}'" if len(components) > 1 else "the part"
        if c.shape.isNull() or not c.shape.Solids:
            report(rel, "invalid-shape", f"{what} has no solid: build() must return a solid, not faces or wires",
                   line=line_of(path, "def build"))
            ok = False
        elif not c.shape.isValid():
            report(rel, "invalid-shape", f"{what} isn't a valid solid (a boolean went wrong): call removeSplitter() "
                   "after fusing, and check the shapes you combine", line=line_of(path, "def build"))
            ok = False
    return ok


def check_part(rel: str, path: Path, bed: list[float] | None, profile: dict) -> None:
    source = path.read_text(encoding="utf-8")
    if "PARAMS" not in source or "def build" not in source:
        report(rel, "contract", "a part defines PARAMS (a frozen dataclass of its dimensions, each named with its "
               "unit, e.g. width_mm) and build(params) returning a Part.Shape", line=1)
        return
    try:
        components = load(rel, ROOT)
    except LoadError as e:
        report(rel, "build-error", str(e), line=line_of(path, "def build"))
        return
    if not valid(rel, path, components):
        return
    shape = components[0].shape
    box = shape.BoundBox
    density = module_flag(path, "DENSITY_G_CM3", 1.27)
    density = density if isinstance(density, (int, float)) else 1.27
    report(rel, "summary", f"{box.XLength:.1f} x {box.YLength:.1f} x {box.ZLength:.1f} mm, "
           f"{shape.Volume / 1000 * density:.0f} g", severity="info")
    if module_flag(path, "PRINTED", True) is False:
        return  # bought, or made another way: not judged as a print
    if bed is not None:
        have = sorted((box.XLength, box.YLength, box.ZLength))
        if any(h > r + 1e-6 for h, r in zip(have, sorted(bed), strict=True)):
            report(rel, "too-large", f"the part is {box.XLength:.1f} x {box.YLength:.1f} x {box.ZLength:.1f} mm; "
                   f"the printer's bed takes {bed[0]:g} x {bed[1]:g} x {bed[2]:g} mm, in any orientation",
                   line=line_of(path, "PARAMS"))
    # what printing and a hand notice: warnings, never failures
    try:
        measured = dfm.measure(shape)
        for f in dfm.judge(measured, {k: v for k, v in profile.items() if k != "max_size_mm"}):
            code = {"thin": "thin-wall"}.get(f.code, f.code)
            report(rel, code, f.message, severity="warning")
    except Exception as e:  # noqa: BLE001
        report(rel, "not-measured", f"the print checks couldn't measure the part: {e}", severity="warning")
    rests = module_flag(path, "RESTS_ON", "-z")
    down = dfm.vec(rests) if rests in dfm.AXES else dfm.vec("-z")
    try:
        sharp = appearance.sharp_outer_edges(shape, down)
    except Exception:  # noqa: BLE001
        sharp = []
    if sharp:
        total = sum(length for _, length, _ in sharp)
        worst = max(sharp, key=lambda s: s[1])
        report(rel, "sharp-edge", f"{len(sharp)} sharp outer edge(s), {total:.0f} mm in all, the longest at "
               f"{dfm.where(worst[0])}. Leave them if a hand never meets them (faces against another part)",
               severity="warning")


def check_assembly(rel: str, path: Path) -> None:
    try:
        components = load(rel, ROOT)
    except LoadError as e:
        report(rel, "build-error", str(e), line=line_of(path, "def build"))
        return
    if len(components) < 1:
        report(rel, "contract", "an assembly's build() returns its placed components: a dict of name -> "
               "Part.Shape", line=line_of(path, "def build"))
        return
    if not valid(rel, path, components):
        return
    at = line_of(path, "def build")
    engaged: dict[str, float] = {}
    alike: dict[tuple, list[str]] = {}  # overlaps of the same kind: one problem, many places
    for a, b, shared in overlaps(components, OVERLAP_MM3, engaged):
        c = shared.BoundBox
        kind = (a.rsplit(":", 1)[0], b.rsplit(":", 1)[0], round(shared.Volume, 1))
        alike.setdefault(kind, []).append(
            f"'{a}' and '{b}' occupy the same space: {shared.Volume:,.2f} mm³ at "
            f"x {c.XMin:.1f}..{c.XMax:.1f}, y {c.YMin:.1f}..{c.YMax:.1f}, z {c.ZMin:.1f}..{c.ZMax:.1f}"
        )
    for found in alike.values():
        more = f" The same overlap is at {len(found) - 1} more place(s) like it: one cause." if len(found) > 1 else ""
        report(rel, "overlap", f"{found[0]}.{more} Render the assembly to see it", line=at)
    for name, mm in engaged.items():
        std = screw_of(name)
        need = fasteners.diameter(std.thread) * fasteners.ENGAGEMENT_DIAMETERS
        if mm + 1e-6 < need:
            report(rel, "thread-engagement", f"'{name}' has {mm:.1f} mm of thread in its tapped hole; an {std.thread} "
                   f"needs at least {need:g} mm. Use a longer screw or a deeper hole", line=at)
    near: dict[str, set[str]] = {}
    for screw in (c for c in components if screw_of(c.name)):
        near[screw.name] = set()
        reach = screw.shape.BoundBox
        reach.enlarge(NEAR_MM)
        for other in components:
            if other is screw or screw_of(other.name) or not reach.intersect(other.shape.BoundBox):
                continue
            try:
                if screw.shape.distToShape(other.shape)[0] <= NEAR_MM:
                    near[screw.name].add(other.name)
            except Exception:  # noqa: BLE001
                pass
    for name, parts in near.items():
        if name not in engaged and len(parts) < 2:
            reach = f"only '{next(iter(parts))}'" if parts else "no part"
            report(rel, "screw-holds-nothing", f"'{name}' reaches {reach}: a screw joins two parts. Render with "
                   f"focus '{name}' to see where it is", severity="warning")
    lo = [min(getattr(c.shape.BoundBox, k) for c in components) for k in ("XMin", "YMin", "ZMin")]
    hi = [max(getattr(c.shape.BoundBox, k) for c in components) for k in ("XMax", "YMax", "ZMax")]
    report(rel, "summary", f"{len(components)} components, {hi[0] - lo[0]:.1f} x {hi[1] - lo[1]:.1f} x "
           f"{hi[2] - lo[2]:.1f} mm overall", severity="info")


def main() -> int:
    bed = printer_bed(ROOT)
    profile = dfm.load_profiles(ROOT).get("fdm", {})
    parts = sorted(p for p in (ROOT / "parts").glob("*.py") if p.name != "__init__.py")
    if parts and bed is None:
        report("design/printer.toml", "no-printer", "no design/printer.toml with bed_mm = [x, y, z]: parts aren't "
               "checked against your printer's bed", severity="warning")
    for path in parts:
        check_part(path.relative_to(ROOT).as_posix(), path, bed, profile)
    for path in sorted(p for p in (ROOT / "assemblies").glob("*.py") if p.name != "__init__.py"):
        check_assembly(path.relative_to(ROOT).as_posix(), path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
