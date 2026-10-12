"""Engineering checks for FreeCAD parts: deterministic, no model involved.

Every module in parts/ is one part:
    PARAMS   an instance of a dataclass: the part's dimensions, each named with its unit
    build(p) returns the part as a Part.Shape
Optional:
    PARAM_RANGES     {"wall_mm": (1.2, 4.0)}: the range the part must build across
    DENSITY_G_CM3    for a mass estimate
Checked: the contract, units in parameter names, that it builds, a valid solid, that it
still builds when each dimension changes (±10%, or across PARAM_RANGES), STEP export, a test
file per part, the spec's targets (design/<part>.spec.toml): its envelope and its mass, the
standard sizes it declares, and that it can be made by every process it names (dfm.py).

Every module in assemblies/ is one assembly: build() returns its placed components, name ->
Part.Shape. Checked against its spec: each part placed as often as the spec says, no two
components in the same space, fixed joints meeting, moving joints keeping their clearance. One JSON object per line: file, line, code, message, severity."""

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
    """Where `needle` is defined (a dataclass field `name: ...`, or `def name`), else its
    first occurrence as a whole word: never a docstring line that merely contains it."""
    import re

    lines = source.splitlines()
    for pattern in (rf"^\s*{re.escape(needle)}\s*:", rf"^\s*def\s+{re.escape(needle)}\b", rf"\b{re.escape(needle)}\b"):
        for n, text in enumerate(lines, 1):
            if re.search(pattern, text):
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
        report(rel, "invalid-shape" if "invalid" in problem else "no-solid", problem, line_of(source, "build"))
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
            report(rel, "export-failed", f"STEP export fails: {e}", line_of(source, "build"))

    bb = extent(shape)
    info = f"{shape.Volume:,.1f} mm³, {bb.XLength:.2f} x {bb.YLength:.2f} x {bb.ZLength:.2f} mm"
    density = getattr(module, "DENSITY_G_CM3", None)
    if isinstance(density, (int, float)):
        info += f", {shape.Volume / 1000 * density:.1f} g at {density} g/cm³"
    design = load_spec(root, path.stem)
    material = materials.get(str(design.get("material"))) if materials is not None else None
    if material is not None:
        if not isinstance(density, (int, float)):
            density = material.density_g_cm3  # the library's: the part needn't repeat it
            info += f", {shape.Volume / 1000 * density:.1f} g in {material.name}"
        elif abs(density - material.density_g_cm3) > 0.02 * material.density_g_cm3:
            report(rel, "density-mismatch", f"DENSITY_G_CM3 is {density}, but the spec's material {material.name} "
                   f"is {material.density_g_cm3} g/cm³: remove the constant, or correct the material",
                   line_of(source, "DENSITY_G_CM3"))
    report(rel, "summary", info, severity="info")
    targets(root, path.stem, rel, shape, density)
    standard_sizes(root, path.stem, design, params)
    manufacturable(root, rel, design, shape)
    holdable(root, rel, path.stem, design, params)
    strong(root, path.stem, design, params)
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import appearance

    for finding in appearance.judge(root, shape, design, params):
        report(rel, finding.code, finding.message, 1)

    if not (root / "tests" / f"test_{path.stem}.py").is_file():
        report(rel, "missing-test", f"no tests/test_{path.stem}.py: every part has a test that builds it and "
               "checks what matters (dimensions, volume, holes)", 1)


sys.path.insert(0, str(Path.cwd()))  # the project's standards/ package, shipped with the ruleset
try:
    from standards import fasteners, materials, sizes
except ImportError:  # a project from before the standards library: those checks are skipped
    fasteners = materials = sizes = None
try:
    from standards import tolerances
except ImportError:
    tolerances = None


def tolerance_of(design: dict, param: str, value: float):
    """How a parameter is toleranced, from its part's spec: (smallest size, largest size, how
    it's said, the spec's entry or None). None: it has no tolerance. The entry of the spec
    wins, then a clearance hole's class (ISO 273), then the spec's general tolerance."""
    if tolerances is None:
        return None
    try:
        for entry in design.get("tolerances", []) if isinstance(design.get("tolerances"), list) else []:
            if entry.get("parameter") != param:
                continue
            if isinstance(entry.get("fit"), str):
                low, high = tolerances.limits(entry["fit"], value)
                return value + low, value + high, entry["fit"], entry
            if isinstance(entry.get("general"), str):
                by = tolerances.general(entry["general"], value)
                return value - by, value + by, f"ISO 2768-{entry['general']}", entry
            if isinstance(entry.get("upper_mm"), (int, float)) and isinstance(entry.get("lower_mm"), (int, float)):
                said = f"{entry['upper_mm']:+g}/{entry['lower_mm']:+g} mm"
                return value + entry["lower_mm"], value + entry["upper_mm"], said, entry
        for entry in design.get("standards", []) if isinstance(design.get("standards"), list) else []:
            if entry.get("parameter") == param and entry.get("standard") == "clearance_hole":
                cls = tolerances.CLEARANCE_HOLE.get(entry.get("fit") or "medium", "H13")
                low, high = tolerances.limits(cls, value)
                return value + low, value + high, f"{cls} (ISO 273)", None
        if isinstance(design.get("general_tolerance"), str):
            by = tolerances.general(design["general_tolerance"], value)
            return value - by, value + by, f"ISO 2768-{design['general_tolerance']}", None
    except (tolerances.UnknownClass, KeyError, TypeError):
        return None
    return None


def holdable(root: Path, rel: str, name: str, design: dict, params) -> None:
    """The process can hold what the spec asks: a tolerance finer than the process's grade
    needs a second operation, named in the spec (achieved_by)."""
    if tolerances is None:
        return
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import dfm

    profiles = dfm.load_profiles(root)
    asked = {e.get("parameter") for e in design.get("tolerances", []) if isinstance(e, dict)} if isinstance(design.get("tolerances"), list) else set()
    for i in design.get("interfaces", []) if isinstance(design.get("interfaces"), list) else []:
        asked |= {n for n in i.get("parameters", []) if isinstance(n, str)} if isinstance(i, dict) and isinstance(i.get("parameters"), list) else set()
    spec_rel = f"design/{name}.spec.toml"
    for param in sorted(p for p in asked if isinstance(p, str)):
        value = getattr(params, param, None)
        if not isinstance(value, (int, float)) or value <= 0:
            continue
        found = tolerance_of(design, param, float(value))
        if found is None:
            continue
        low, high, said, entry = found
        for process in design.get("processes", []) if isinstance(design.get("processes"), list) else []:
            profile = profiles.get(process)
            best = profile.get("best_tolerance_grade") if isinstance(profile, dict) else None
            if not isinstance(best, int):
                continue
            try:
                holds = tolerances.grade_mm(best, float(value))
            except tolerances.UnknownClass:
                continue
            if high - low >= holds - 1e-9:
                continue
            title = profile.get("title", process)
            how = entry.get("achieved_by") if isinstance(entry, dict) else None
            if isinstance(how, str) and how.strip():
                report(spec_rel, "tolerance-by-second-operation", f"{param} ({said}, a band of {high - low:.3f} mm) "
                       f"is finer than {title} holds; achieved by: {how.strip()}", severity="info")
            else:
                report(spec_rel, "tolerance-too-tight", f"{param} is toleranced {said}: a band of {high - low:.3f} mm "
                       f"at {value:g} mm. {title} holds about IT{best} ({holds:.3f} mm at this size). Loosen it, or "
                       "name the operation that achieves it in the spec (achieved_by = \"reamed\")", 1)


def strong(root: Path, name: str, design: dict, params) -> None:
    """The loads the spec states ([[loads]]), calculated by hand on the part's parameters:
    each must reach its safety factor, and stay within the deflection it allows."""
    if materials is None or not design.get("loads"):
        return
    try:
        from standards import strength
    except ImportError:
        return
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import dfm
    import loads

    spec_rel = f"design/{name}.spec.toml"
    for result in loads.evaluate(design, params, dfm.load_profiles(root), strength, materials):
        for code, message in result.findings:
            report(spec_rel, code, message, 1)
        if result.ok:
            report(spec_rel, "load-carried", f"load {result.ident}: {result.said}", severity="info")


def manufacturable(root: Path, rel: str, design: dict, shape) -> None:
    """Design for manufacturing: the built part against the profile of every process its spec
    names (dfm.py measures, processes.toml and the project's design/processes.toml judge)."""
    processes = design.get("processes")
    if not isinstance(processes, list) or not processes:
        return
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import dfm

    profiles = dfm.load_profiles(root)
    orientation = design.get("orientation")
    up = orientation.get("up", "+z") if isinstance(orientation, dict) else "+z"
    if up not in dfm.AXES:
        up = "+z"
    measured = None
    for process in processes:
        profile = profiles.get(process)
        if not isinstance(profile, dict):
            continue  # the spec check says the process is unknown
        if measured is None:
            measured = dfm.measure(shape)
        title = profile.get("title", process)
        for finding in dfm.judge(measured, profile, up):
            report(rel, finding.code, f"{title}: {finding.message}", 1)


def standard_sizes(root: Path, name: str, design: dict, params) -> None:
    """The parameters the spec declares to follow a standard ([[standards]]) have a value the
    standard allows; one that doesn't needs its reason stated there."""
    if sizes is None:
        return
    spec_rel = f"design/{name}.spec.toml"
    for entry in design.get("standards", []) if isinstance(design.get("standards"), list) else []:
        param, kind = entry.get("parameter"), entry.get("standard")
        value = getattr(params, str(param), None)
        if kind not in sizes.KINDS or not isinstance(value, (int, float)):
            continue  # the spec check says what's wrong with the entry
        try:
            wrong = sizes.check(kind, float(value), entry.get("thread"), entry.get("fit"))
        except (KeyError, ValueError):
            continue
        if wrong is None:
            continue
        reason = entry.get("reason")
        if isinstance(reason, str) and reason.strip():
            report(spec_rel, "nonstandard-accepted", f"{param} is {value:g} mm, not a standard size ({wrong}); "
                   f"the stated reason: {reason.strip()}", severity="info")
        else:
            report(spec_rel, "nonstandard-size", f"{param} is {value:g} mm: {wrong}. Use a standard value, or give "
                   "the reason for this one in the spec (reason = \"...\")", 1)


def extent(shape):
    """The shape's true bounding box. The quick one (shape.BoundBox) is loose on rounded
    surfaces: a 35 mm bar with rounded ends would measure 37.9 mm."""
    try:
        return shape.optimalBoundingBox(False, False)
    except Exception:  # noqa: BLE001
        return shape.BoundBox


def targets(root: Path, name: str, rel: str, shape, density) -> None:
    """The spec's targets, measured on the built part: the envelope it must stay within and
    the mass it must stay under (design/<part>.spec.toml; its form is check_spec.py's job)."""
    import tomllib

    spec_path = root / "design" / f"{name}.spec.toml"
    try:
        spec = tomllib.loads(spec_path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return
    spec_rel = spec_path.relative_to(root).as_posix()
    envelope = spec.get("envelope_mm")
    if isinstance(envelope, dict) and all(isinstance(envelope.get(a), (int, float)) for a in "xyz"):
        bb = extent(shape)
        # the part may lie any way round in its envelope: compare the sizes sorted
        have = sorted((bb.XLength, bb.YLength, bb.ZLength))
        room = sorted(float(envelope[a]) for a in "xyz")
        if any(h > r + 1e-6 for h, r in zip(have, room)):
            report(spec_rel, "over-envelope",
                   f"the part is {bb.XLength:.2f} x {bb.YLength:.2f} x {bb.ZLength:.2f} mm, outside its envelope of "
                   f"{envelope['x']:g} x {envelope['y']:g} x {envelope['z']:g} mm (compared in any orientation)", 1)
    mass = spec.get("mass_g")
    if isinstance(mass, dict) and isinstance(mass.get("max"), (int, float)):
        if not isinstance(density, (int, float)):
            report(rel, "mass-unknown", "the spec sets a mass target, but the part has no DENSITY_G_CM3 to "
                   "work its mass out from", 1)
        else:
            grams = shape.Volume / 1000 * density
            if grams > mass["max"] + 1e-9:
                report(spec_rel, "over-mass", f"the part weighs {grams:.1f} g, over its target of {mass['max']:g} g", 1)


# --- assemblies -------------------------------------------------------------------
OVERLAP_MM3 = 1e-3  # two solids sharing more than this are in each other's way
TOUCHING_MM = 0.5  # a fixed joint's parts are at most this far apart, unless its spec says max_gap_mm
MOVING = ("sliding", "rotating")


def load_spec(root: Path, name: str) -> dict:
    import tomllib

    try:
        return tomllib.loads((root / "design" / f"{name}.spec.toml").read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return {}


def instances(components: dict, name: str) -> list[str]:
    """The placed components of one part: "<name>", or "<name>:1", "<name>:2" for several."""
    return [k for k in components if k == name or k.startswith(f"{name}:")]


def joint_end(components: dict, end: str) -> list[str]:
    """The placed components a joint's end means: <part>:<interface>, reference:<file> or
    standard:<designation> (standard parts needn't be modelled: then none)."""
    kind, _, rest = end.partition(":")
    if kind == "reference":
        return instances(components, Path(rest).stem)
    if kind == "standard":
        return [k for k in components if k == end or k.startswith(f"{end}:")]
    return instances(components, kind)


def part_dimension(root: Path, text: str, cache: dict):
    """(smallest, largest, how said) of <part>:<parameter>, from that part's PARAMS and spec."""
    part, _, param = text.lstrip("+-").partition(":")
    if part not in cache:
        path = root / "parts" / f"{part}.py"
        spec = importlib.util.spec_from_file_location(f"parts_for_fits_{part}", path)
        try:
            assert spec and spec.loader
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            cache[part] = (getattr(module, "PARAMS", None), load_spec(root, part))
        except Exception:  # noqa: BLE001  (the part's own check reports it)
            cache[part] = (None, {})
    params, design = cache[part]
    value = getattr(params, param, None)
    if not isinstance(value, (int, float)):
        return None
    found = tolerance_of(design, param, float(value))
    return None if found is None else (found[0], found[1], found[2], float(value))


def fits_and_stacks(root: Path, name: str, design: dict) -> None:
    """Tolerances across parts, worst case: a joint's fit is the fit its spec says, and every
    chain of dimensions (a stack) stays within its limits when each part is at its worst."""
    if tolerances is None:
        return
    spec_rel = f"design/{name}.spec.toml"
    cache: dict = {}

    def untoleranced(what: str, text: str) -> None:
        report(spec_rel, "untoleranced", f"{what}: {text.lstrip('+-')} has no tolerance, so the worst case can't "
               "be worked out: tolerance it in its part's spec (or give that spec a general_tolerance)", 1)

    for n, joint in enumerate((j for j in design.get("joints", []) if isinstance(j, dict)), 1):
        fit = joint.get("fit")
        if not isinstance(fit, dict) or not isinstance(fit.get("hole"), str) or not isinstance(fit.get("shaft"), str):
            continue
        hole, shaft = part_dimension(root, fit["hole"], cache), part_dimension(root, fit["shaft"], cache)
        if hole is None or shaft is None:
            untoleranced(f"joint {n}'s fit", fit["hole"] if hole is None else fit["shaft"])
            continue
        least, most, kind = tolerances.fit(hole[:2], shaft[:2])
        described = (f"hole {hole[3]:g} {hole[2]} ({hole[0]:.3f} to {hole[1]:.3f}), shaft {shaft[3]:g} {shaft[2]} "
                     f"({shaft[0]:.3f} to {shaft[1]:.3f}): clearance from {least:+.3f} to {most:+.3f} mm")
        wanted = fit.get("kind")
        if wanted in ("clearance", "transition", "interference") and kind != wanted:
            report(spec_rel, "fit", f"joint {n} should be a {wanted} fit, but is a {kind} fit. {described}", 1)
            continue
        low, high = fit.get("min_clearance_mm"), fit.get("max_clearance_mm")
        if isinstance(low, (int, float)) and least < low - 1e-9:
            report(spec_rel, "fit", f"joint {n}: the least clearance is {least:+.3f} mm, under the {low:g} mm it "
                   f"needs. {described}", 1)
        elif isinstance(high, (int, float)) and most > high + 1e-9:
            report(spec_rel, "fit", f"joint {n}: the most clearance is {most:+.3f} mm, over the {high:g} mm it "
                   f"may have. {described}", 1)
        else:
            report(spec_rel, "fit-summary", f"joint {n}: a {kind} fit. {described}", severity="info")

    for stack in (s for s in design.get("stacks", []) if isinstance(s, dict)):
        ident, terms = stack.get("id", "?"), stack.get("terms")
        if not isinstance(terms, list) or any(not isinstance(t, str) or not t or t[0] not in "+-" for t in terms):
            continue
        least = most = nominal = 0.0
        ok = True
        for term in terms:
            found = part_dimension(root, term, cache)
            if found is None:
                untoleranced(f"stack {ident}", term)
                ok = False
                break
            sign = 1 if term[0] == "+" else -1
            nominal += sign * found[3]
            least += found[0] if sign > 0 else -found[1]
            most += found[1] if sign > 0 else -found[0]
        if not ok:
            continue
        said = f"{nominal:.3f} mm nominally, from {least:.3f} to {most:.3f} mm in the worst case"
        low, high = stack.get("min_mm"), stack.get("max_mm")
        if isinstance(low, (int, float)) and least < low - 1e-9:
            report(spec_rel, "stack-up", f"stack {ident} ({' '.join(terms)}) is {said}: under its minimum of "
                   f"{low:g} mm. Tighten the dimensions that contribute most, or change the nominal", 1)
        elif isinstance(high, (int, float)) and most > high + 1e-9:
            report(spec_rel, "stack-up", f"stack {ident} ({' '.join(terms)}) is {said}: over its maximum of "
                   f"{high:g} mm. Tighten the dimensions that contribute most, or change the nominal", 1)
        else:
            report(spec_rel, "stack-summary", f"stack {ident}: {said}", severity="info")


ACCESS_MM = 25.0  # the room a hex key needs above a screw's head, at least
ACCESS_DIAMETERS = 6.0  # ... or this many thread diameters, whichever is more


def screw_axis(shape):
    """Where a placed screw's head is and which way it points: (the centre of the head's top
    face, the unit vector from the shank towards the head), read from its geometry."""
    import Part

    cylinders = [f for f in shape.Faces if isinstance(f.Surface, Part.Cylinder)]
    if len(cylinders) < 2:
        return None
    head = max(cylinders, key=lambda f: f.Surface.Radius)
    shank = min(cylinders, key=lambda f: f.Surface.Radius)
    direction = head.CenterOfMass - shank.CenterOfMass
    if direction.Length < 1e-9:
        return None
    direction.normalize()
    centre = head.CenterOfMass
    top = max((v.Point for v in head.Vertexes), key=lambda pt: (pt - centre).dot(direction))
    return centre + direction * (top - centre).dot(direction), direction, head.Surface.Radius


def fastener_checks(rel, source, components, screws, engaged, held_in, root) -> None:
    """Screws hold and can be reached: enough thread engaged in what they screw into, and room
    above the head for the tool."""
    import FreeCAD as App
    import Part

    for name, screw in sorted(screws.items()):
        d = fasteners.diameter(screw.thread)
        if name in held_in:
            need = d * fasteners.ENGAGEMENT_DIAMETERS
            host = held_in[name]
            host_spec = load_spec(root, host.split(":")[0])
            material = materials.get(str(host_spec.get("material"))) if host_spec else None
            if material is not None:
                need = d * material.engagement_diameters
            if engaged.get(name, 0.0) + 1e-6 < need:
                where = f" in {material.name}" if material is not None else ""
                report(rel, "thread-engagement", f"'{name}' has {engaged.get(name, 0.0):.1f} mm of thread in "
                       f"'{host}'; an {screw.thread} screw needs at least {need:g} mm{where}. Use a longer screw "
                       "or a deeper tapped hole", line_of(source, "build"))
        found = screw_axis(components[name])
        if found is None:
            continue
        top, direction, radius = found
        length = max(ACCESS_MM, ACCESS_DIAMETERS * d)
        tool = Part.makeCylinder(radius, length, top + direction * 0.01, App.Vector(direction))
        for other, shape in sorted(components.items()):
            if other == name or other in screws or not tool.BoundBox.intersect(shape.BoundBox):
                continue
            try:
                blocked = tool.common(shape).Volume
            except Exception:  # noqa: BLE001
                blocked = 0.0
            if blocked > OVERLAP_MM3:
                report(rel, "no-tool-access", f"'{name}' can't be reached: '{other}' is in the way of the tool "
                       f"above its head ({length:g} mm of room is needed along the screw's axis)",
                       line_of(source, "build"))
                break


def validate_assembly(path: Path, root: Path) -> None:
    """An assembly: assemblies/<name>.py with build() returning its placed components, name ->
    Part.Shape. Checked against its spec: every part is placed as often as the spec says, no
    two components occupy the same space, fixed joints meet, moving joints keep their
    clearance."""
    import Part

    rel = path.relative_to(root).as_posix()
    source = path.read_text(encoding="utf-8")
    spec = importlib.util.spec_from_file_location(f"assemblies_{path.stem}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
        build = getattr(module, "build", None)
        components = build() if callable(build) else None
    except Exception as e:  # noqa: BLE001
        report(rel, "build-error", f"building the assembly fails: {type(e).__name__}: {e}", error_line(e, path))
        return
    if not isinstance(components, dict) or not components or any(
        not isinstance(k, str) or not isinstance(v, Part.Shape) for k, v in components.items()
    ):
        report(rel, "assembly-contract", "an assembly defines build() returning its placed components as a "
               "dict: name -> Part.Shape, each already in position", line_of(source, "build") or 1)
        return
    for name, shape in components.items():
        problem = check_shape(shape, f"component '{name}'")
        if problem:
            report(rel, "invalid-shape" if "invalid" in problem else "no-solid", problem, line_of(source, "build"))
            return

    design = load_spec(root, path.stem)
    wanted = [m for m in design.get("parts", []) if isinstance(m, dict)]
    known: set[str] = set()
    for m in wanted:
        if isinstance(m.get("part"), str) or isinstance(m.get("reference"), str):
            name = m["part"] if isinstance(m.get("part"), str) else Path(m["reference"]).stem
            placed = instances(components, name)
            known |= set(placed)
            quantity = m.get("quantity", 1) if isinstance(m.get("quantity", 1), int) else 1
            if len(placed) != quantity:
                how = f'"{name}"' if quantity == 1 else f'"{name}:1" to "{name}:{quantity}"'
                report(rel, "component-missing", f"the spec has {quantity} x {name}, build() places {len(placed)}: "
                       f"return {how}", line_of(source, "build"))
    screws: dict[str, object] = {}  # placed component -> the standard screw it is
    for m in wanted:
        std = fasteners.parse(str(m.get("standard"))) if fasteners is not None and isinstance(m.get("standard"), str) else None
        if std is None or std.kind != "screw" or fasteners.problems(std.designation):
            continue
        key = f"standard:{std.designation}"
        placed = [k for k in components if k == key or k.startswith(f"{key}:")]
        screws.update({k: std for k in placed})
        quantity = m.get("quantity", 1) if isinstance(m.get("quantity", 1), int) else 1
        if len(placed) != quantity:
            how = f'"{key}"' if quantity == 1 else f'"{key}:1" to "{key}:{quantity}"'
            report(rel, "component-missing", f"the spec has {quantity} x {std.designation}, build() places "
                   f"{len(placed)}: build each with standards.shapes.from_designation and return {how}",
                   line_of(source, "build"))
    for name in components:
        if design and name not in known and not name.startswith("standard:"):
            report(rel, "component-unknown", f"build() places '{name}', which the spec doesn't list: add it to "
                   f"design/{path.stem}.spec.toml, or remove it", line_of(source, name) or line_of(source, "build"))

    # nothing occupies the same space
    engaged: dict[str, float] = {}  # screw -> mm of thread engaged
    held_in: dict[str, str] = {}
    names = sorted(components)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            sa, sb = components[a], components[b]
            if not sa.BoundBox.intersect(sb.BoundBox):
                continue
            try:
                shared = sa.common(sb)
                volume = shared.Volume if not shared.isNull() else 0.0
            except Exception:  # noqa: BLE001
                volume = 0.0
            # a screw in a tapped hole shares the thread's depth with it: that much is engagement
            screw = screws.get(a) or screws.get(b)
            if screw is not None and not (a in screws and b in screws):
                other = b if a in screws else a
                d, core = fasteners.diameter(screw.thread), fasteners.tap_drill(screw.thread)
                thread_mm3 = 3.141592653589793 / 4 * (d * d - core * core) * screw.length_mm
                if volume <= thread_mm3 * 1.02 + OVERLAP_MM3:
                    which = a if a in screws else b
                    engaged[which] = engaged.get(which, 0.0) + volume / (thread_mm3 / screw.length_mm)
                    held_in[which] = other
                    continue
            if volume > OVERLAP_MM3:
                c = shared.BoundBox.Center
                report(rel, "interference", f"'{a}' and '{b}' occupy the same space: {volume:,.2f} mm³ overlap "
                       f"around x {c.x:.1f}, y {c.y:.1f}, z {c.z:.1f} mm", line_of(source, "build"))

    # joints: fixed ones meet, moving ones keep their clearance
    for n, joint in enumerate((j for j in design.get("joints", []) if isinstance(j, dict)), 1):
        ends_a = joint_end(components, str(joint.get("a", "")))
        ends_b = joint_end(components, str(joint.get("b", "")))
        kind = joint.get("kind", "fixed")
        for a in ends_a:
            for b in ends_b:
                if a == b:
                    continue
                gap = components[a].distToShape(components[b])[0]
                if kind in MOVING:
                    need = joint.get("clearance_mm", 0.0)
                    if isinstance(need, (int, float)) and gap + 1e-9 < need:
                        report(rel, "clearance", f"joint {n} ({kind}): '{a}' and '{b}' are {gap:.2f} mm apart, "
                               f"less than the {need:g} mm they need to move", line_of(source, "build"))
                else:
                    most = joint.get("max_gap_mm", TOUCHING_MM)
                    if isinstance(most, (int, float)) and gap > most + 1e-9:
                        report(rel, "joint-open", f"joint {n}: '{a}' and '{b}' are joined in the spec but "
                               f"{gap:.2f} mm apart (at most {most:g} mm)", line_of(source, "build"))

    fastener_checks(rel, source, components, screws, engaged, held_in, root)
    fits_and_stacks(root, path.stem, design)

    box = None
    for shape in components.values():
        box = extent(shape) if box is None else box.united(extent(shape))
    assert box is not None
    report(rel, "summary", f"{len(components)} components, {box.XLength:.2f} x {box.YLength:.2f} x "
           f"{box.ZLength:.2f} mm overall", severity="info")
    if not (root / "tests" / f"test_{path.stem}.py").is_file():
        report(rel, "missing-test", f"no tests/test_{path.stem}.py: every assembly has a test that builds it and "
               "checks what matters (what touches what, what clears what)", 1)


PYTHON_HOMES = ("parts/", "assemblies/", "tests/", "scripts/", "standards/")


def misplaced(root: Path) -> None:
    """Python outside parts/, tests/ and scripts/ is checked by nothing here: a part in
    src/parts/ would pass every run unseen. So it's an error, with where it belongs."""
    import subprocess

    listed = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard", "*.py"],
                            cwd=root, capture_output=True, text=True)
    if listed.returncode == 0:
        files = listed.stdout.splitlines()
    else:
        files = [p.relative_to(root).as_posix() for p in root.rglob("*.py")]
    for rel in sorted(files):
        if rel.startswith((*PYTHON_HOMES, ".codecrew/")) or "/" not in rel and rel == "conftest.py":
            continue
        name = rel.rsplit("/", 1)[-1]
        home = "tests/" if name.startswith("test_") or name == "conftest.py" else "parts/"
        report(rel, "outside-parts", f"Python lives in parts/, assemblies/, tests/ or scripts/ here: nothing checks "
               f"{rel} where it is. Move it to {home}{name}.", 1)


def main() -> int:
    root = Path.cwd()
    parts_dir = root / (sys.argv[1] if len(sys.argv) > 1 else "parts")
    sys.path.insert(0, str(root))
    misplaced(root)
    for path in sorted(parts_dir.glob("*.py")):
        if path.name != "__init__.py":
            validate(path, root)
    assemblies = root / "assemblies"
    for path in sorted(assemblies.glob("*.py")) if assemblies.is_dir() else []:
        if path.name != "__init__.py":
            validate_assembly(path, root)
    return 0


if __name__ == "__main__":
    sys.exit(main())
