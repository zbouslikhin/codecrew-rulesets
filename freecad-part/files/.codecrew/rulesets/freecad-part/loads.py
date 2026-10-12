"""Load cases: what a part must carry, said in its spec and checked by hand calculation.

    safety_factor = 2.0          # how many times the load it must take; a load may set its own

    [[loads]]
    id = "L1"
    text = "The sensor's weight in a 5 g shock, at the top of the wall"
    model = "cantilever"
    force_n = 15.0
    length = "height_mm"                                  # dimensions are parameters of Params
    section = { shape = "rectangle", width = "width_mm", height = "thickness_mm" }
    max_deflection_mm = 1.0                               # optional
    stress_concentration = 1.5                            # optional: a notch, a hole, a sharp corner

The models (standards/strength.py has the formulas):

    cantilever          force_n, length, section            fixed at one end, the force at the other
    simply_supported    force_n, span, section              on two supports, the force in the middle
    tension             force_n, section                    pulled or pushed along its axis
    screws_in_shear     force_n, thread, count, planes, property_class
    snap_arm            deflection, length, thickness       repeated = true for a joint opened often

A section is { shape = "rectangle", width, height } (height along the load), { shape =
"round", diameter } or { shape = "tube", outer, inner }.

The material's strength comes from standards.materials, reduced by the process's
strength_factor (processes.toml: a printed part is weaker than the filament's datasheet).
Nothing here imports FreeCAD: the spec check uses problems(), the geometry check and the
report use evaluate().
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

SECTIONS: dict[str, tuple[str, ...]] = {
    "rectangle": ("width", "height"),
    "round": ("diameter",),
    "tube": ("outer", "inner"),
}
# model -> (the dimensions it takes from Params, does it need a section, does it need force_n)
MODELS: dict[str, tuple[tuple[str, ...], bool, bool]] = {
    "cantilever": (("length",), True, True),
    "simply_supported": (("span",), True, True),
    "tension": ((), True, True),
    "screws_in_shear": ((), False, True),
    "snap_arm": (("deflection", "length", "thickness"), False, False),
}
MIN_SAFETY_FACTOR = 1.0


def _number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def loads_of(design: dict) -> list[dict]:
    value = design.get("loads", [])
    return [v for v in value if isinstance(v, dict)] if isinstance(value, list) else []


def target_of(design: dict, load: dict) -> float | None:
    for source in (load, design):
        if _number(source.get("safety_factor")):
            return float(source["safety_factor"])
    return None


def dimensions(load: dict) -> list[tuple[str, object]]:
    """Every dimension the load names, as (what it is, the parameter it names)."""
    model = MODELS.get(str(load.get("model")))
    if model is None:
        return []
    named = [(key, load.get(key)) for key in model[0]]
    section = load.get("section")
    if model[1] and isinstance(section, dict):
        named += [(f"section.{key}", section.get(key)) for key in SECTIONS.get(str(section.get("shape")), ())]
    return named


def problems(design: dict, load: dict, params: set[str] | None, threads, classes) -> list[tuple[str, str]]:
    """What is wrong with a load as written: (code, message). `params` is the part's Params
    (None when the part isn't built yet); threads and classes are the ones the library knows."""
    ident = str(load.get("id") or "?")
    found: list[tuple[str, str]] = []

    def say(code: str, message: str) -> None:
        found.append((code, f"load {ident}: {message}"))

    if not (isinstance(load.get("text"), str) and load["text"].strip()):
        say("spec-incomplete", "say in text what the load is and where it comes from")
    model = MODELS.get(str(load.get("model")))
    if model is None:
        say("unknown-load-model", f"model is one of {', '.join(MODELS)}, not {load.get('model')!r}")
        return found
    names, needs_section, needs_force = model
    if needs_force and not (_number(load.get("force_n")) and load["force_n"] > 0):
        say("spec-incomplete", "force_n is missing: the force in newtons, a positive number")
    if needs_section:
        section = load.get("section")
        if not isinstance(section, dict) or section.get("shape") not in SECTIONS:
            say(
                "spec-invalid",
                'section is e.g. { shape = "rectangle", width = "width_mm", height = "thickness_mm" } '
                f"(shapes: {', '.join(SECTIONS)}; height is the side along the load)",
            )
    for what, name in dimensions(load):
        if not isinstance(name, str) or not name.endswith("_mm"):
            say(
                "spec-invalid",
                f"{what} names a parameter of Params in mm (e.g. {what.split('.')[-1]} = \"length_mm\"), "
                "not a number: the check must follow the part when it changes",
            )
        elif params is not None and name not in params:
            say("unknown-parameter", f"Params has no parameter '{name}' ({what})")
    if load.get("model") == "screws_in_shear":
        if load.get("thread") not in threads:
            say("spec-invalid", 'thread is missing: the screws\' size, e.g. "M4"')
        if load.get("property_class", "8.8") not in classes:
            say("spec-invalid", f"property_class is one of {', '.join(classes)}")
        for key in ("count", "planes"):
            value = load.get(key, 1)
            if not isinstance(value, int) or isinstance(value, bool) or value < 1:
                say("spec-invalid", f"{key} is a whole number, 1 or more")
    for key in ("max_deflection_mm", "stress_concentration"):
        if key in load and not (_number(load[key]) and load[key] > 0):
            say("spec-invalid", f"{key} is a positive number")
    if _number(load.get("stress_concentration")) and load["stress_concentration"] < 1:
        say("spec-invalid", "stress_concentration is 1 or more: a notch never lowers the stress")
    target = target_of(design, load)
    if target is None:
        say(
            "spec-incomplete",
            "no safety factor: give the spec safety_factor (how many times the load the part must "
            "take, e.g. 2.0), or this load its own",
        )
    elif target < MIN_SAFETY_FACTOR:
        say("spec-invalid", f"a safety factor is at least {MIN_SAFETY_FACTOR:g}")
    return found


@dataclass
class Result:
    ident: str
    text: str
    model: str
    said: str = ""  # the calculation in a sentence
    factor: float | None = None  # the safety factor reached
    target: float | None = None
    findings: list[tuple[str, str]] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.findings


def knockdown(design: dict, profiles: dict) -> tuple[float, str]:
    """How much of the material's strength the process leaves: the lowest strength_factor of
    the spec's processes."""
    factor, by = 1.0, ""
    processes = design.get("processes")
    for process in processes if isinstance(processes, list) else []:
        profile = profiles.get(process)
        value = profile.get("strength_factor") if isinstance(profile, dict) else None
        if _number(value) and 0 < value < factor:
            factor, by = float(value), str(profile.get("title", process))
    return factor, by


def evaluate(design: dict, params, profiles: dict, strength, materials) -> list[Result]:
    """Every load of the spec, calculated on the part's parameters. A load that is written
    wrongly is skipped: the spec check says what is wrong with it."""
    material = materials.get(str(design.get("material")))
    reduce, by = knockdown(design, profiles)
    results: list[Result] = []
    names = {f for f in dir(params) if not f.startswith("_")}
    for load in loads_of(design):
        if problems(design, load, names, strength.fasteners.THREADS, strength.PROPERTY_CLASSES):
            continue
        model = str(load["model"])
        result = Result(str(load["id"]), str(load.get("text", "")), model, target=target_of(design, load))
        results.append(result)
        try:
            dims = {what: float(getattr(params, str(name))) for what, name in dimensions(load)}
            _one(result, load, dims, material, reduce, by, strength)
        except (ValueError, TypeError, ZeroDivisionError) as e:
            result.findings.append(("load-not-calculable", f"load {result.ident} can't be calculated: {e}"))
    return results


def _section(load: dict, dims: dict, strength):
    shape = load["section"]["shape"]
    if shape == "rectangle":
        return strength.rectangle(dims["section.width"], dims["section.height"])
    if shape == "round":
        return strength.round_bar(dims["section.diameter"])
    return strength.tube(dims["section.outer"], dims["section.inner"])


def _one(result: Result, load: dict, dims: dict, material, reduce: float, by: str, strength) -> None:
    ident, target = result.ident, result.target or MIN_SAFETY_FACTOR
    model = result.model
    if model == "screws_in_shear":
        cls = str(load.get("property_class", "8.8"))
        count, planes = int(load.get("count", 1)), int(load.get("planes", 1))
        case = strength.screws_in_shear(load["force_n"], load["thread"], count, planes)
        allowed = strength.screw_shear_yield(cls)
        result.factor = strength.safety_factor(allowed, case.stress_mpa)
        result.said = (
            f"{load['force_n']:g} N across {count} x {load['thread']} ({cls}): {case.stress_mpa:.1f} MPa in shear, "
            f"{allowed:.0f} MPa allowed; safety factor {_factor(result.factor)}, needs {target:g}"
        )
        if result.factor < target:
            result.findings.append((
                "screw-overloaded",
                f"load {ident}: {result.said}. Use more or larger screws, a higher property class, or take "
                "the shear with a dowel or a shoulder",
            ))
        return
    if material is None:
        raise ValueError("the spec's material isn't in the materials library")
    if model == "snap_arm":
        repeated = load.get("repeated") is True
        strain = strength.snap_arm_strain(dims["deflection"], dims["length"], dims["thickness"])
        allowed = strength.permissible_strain(material.name, material.yield_mpa, material.modulus_gpa, repeated)
        result.factor = strength.safety_factor(allowed, strain)
        often = ", opened often" if repeated else ""
        result.said = (
            f"an arm {dims['length']:g} mm long and {dims['thickness']:g} mm thick, pushed aside "
            f"{dims['deflection']:g} mm: {strain:.2%} strain at its root, {allowed:.2%} permissible for "
            f"{material.name}{often}; safety factor {_factor(result.factor)}, needs {target:g}"
        )
        if result.factor < target:
            result.findings.append((
                "overstrained",
                f"load {ident}: {result.said}. Make the arm longer or thinner, or the hook shallower",
            ))
        return
    section = _section(load, dims, strength)
    if model == "cantilever":
        case = strength.cantilever(load["force_n"], dims["length"], section, material.modulus_gpa)
        where = f"at the end of {dims['length']:g} mm"
    elif model == "simply_supported":
        case = strength.simply_supported(load["force_n"], dims["span"], section, material.modulus_gpa)
        where = f"in the middle of {dims['span']:g} mm"
    else:
        case = strength.tension(load["force_n"], section)
        where = "along its axis"
    notch = float(load.get("stress_concentration", 1.0))
    stress = case.stress_mpa * notch
    allowed = material.yield_mpa * reduce
    result.factor = strength.safety_factor(allowed, stress)
    allowed_said = f"{allowed:.0f} MPa allowed ({material.name}, {material.yield_mpa:g} MPa"
    allowed_said += f" x {reduce:g} for {by})" if reduce < 1 else ")"
    result.said = (
        f"{load['force_n']:g} N {where}, {section.said}: {stress:.1f} MPa"
        + (f" (x {notch:g} for the notch)" if notch != 1 else "")
        + f", {allowed_said}; safety factor {_factor(result.factor)}, needs {target:g}"
    )
    if result.factor < target:
        result.findings.append((
            "overstressed",
            f"load {ident}: {result.said}. Give the section more depth along the load (it counts "
            "squared), shorten the arm, or choose a stronger material",
        ))
    limit = load.get("max_deflection_mm")
    if _number(limit) and case.deflection_mm is not None:
        result.said += f"; it moves {case.deflection_mm:.2f} mm, {limit:g} mm allowed"
        if case.deflection_mm > limit:
            result.findings.append((
                "too-flexible",
                f"load {ident}: under {load['force_n']:g} N it moves {case.deflection_mm:.2f} mm, more than "
                f"the {limit:g} mm allowed ({section.said}, {material.name}, {material.modulus_gpa:g} GPa). "
                "Stiffness goes with the section's depth cubed: deepen it, add a rib, or shorten the arm",
            ))


def _factor(value: float) -> str:
    return "over 100" if value > 100 or math.isinf(value) else f"{value:.1f}"
