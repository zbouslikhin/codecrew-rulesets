"""Strength by hand calculation: the formulas an engineer reaches for before any simulation.

    from standards import strength
    section = strength.rectangle(width_mm=20, height_mm=10)      # height: along the load
    case = strength.cantilever(force_n=100, length_mm=100, section=section, modulus_gpa=210)
    case.stress_mpa, case.deflection_mm                          # 30.0, 0.095

Units throughout: N, mm, MPa (N/mm²); the modulus in GPa, as in standards.materials.

What these are, and are not. Each is the textbook case for a slender, straight member of
constant cross-section, loaded statically, in a material that behaves linearly: a first check
that a section is in the right range. They know nothing of holes, notches or sharp corners
(give a stress concentration factor where there is one), of fatigue, creep, heat, impact or
buckling, and a short stubby part is not a beam. A part whose failure would hurt someone is
analysed and tested properly, whatever these numbers say.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from standards import fasteners


@dataclass(frozen=True)
class Section:
    """A cross-section: its area, its second moment of area about the bending axis, and the
    distance from that axis to the outermost fibre."""

    area_mm2: float
    inertia_mm4: float
    fibre_mm: float
    said: str = ""

    @property
    def modulus_mm3(self) -> float:
        return self.inertia_mm4 / self.fibre_mm


def _positive(**values: float) -> None:
    for name, value in values.items():
        if not isinstance(value, (int, float)) or isinstance(value, bool) or not value > 0:
            raise ValueError(f"{name} must be a positive number, not {value!r}")


def rectangle(width_mm: float, height_mm: float) -> Section:
    """A solid rectangle. height_mm is the side along the load: the one that resists bending."""
    _positive(width_mm=width_mm, height_mm=height_mm)
    return Section(
        width_mm * height_mm,
        width_mm * height_mm**3 / 12,
        height_mm / 2,
        f"rectangle {width_mm:g} x {height_mm:g} mm",
    )


def round_bar(diameter_mm: float) -> Section:
    _positive(diameter_mm=diameter_mm)
    return Section(
        math.pi * diameter_mm**2 / 4,
        math.pi * diameter_mm**4 / 64,
        diameter_mm / 2,
        f"round {diameter_mm:g} mm",
    )


def tube(outer_mm: float, inner_mm: float) -> Section:
    _positive(outer_mm=outer_mm, inner_mm=inner_mm)
    if inner_mm >= outer_mm:
        raise ValueError(
            f"a tube's inner diameter ({inner_mm:g}) must be smaller than its outer ({outer_mm:g})"
        )
    return Section(
        math.pi * (outer_mm**2 - inner_mm**2) / 4,
        math.pi * (outer_mm**4 - inner_mm**4) / 64,
        outer_mm / 2,
        f"tube {outer_mm:g} x {inner_mm:g} mm",
    )


@dataclass(frozen=True)
class Case:
    """What a load does: the highest stress, and how far the member moves (None where the
    model gives none)."""

    stress_mpa: float
    deflection_mm: float | None = None


def cantilever(force_n: float, length_mm: float, section: Section, modulus_gpa: float) -> Case:
    """A beam fixed at one end, the force across its free end, length_mm away.
    Stress at the root: F L / Z. Deflection of the end: F L³ / (3 E I)."""
    _positive(force_n=force_n, length_mm=length_mm, modulus_gpa=modulus_gpa)
    e = modulus_gpa * 1000
    return Case(
        force_n * length_mm / section.modulus_mm3,
        force_n * length_mm**3 / (3 * e * section.inertia_mm4),
    )


def simply_supported(force_n: float, span_mm: float, section: Section, modulus_gpa: float) -> Case:
    """A beam resting on two supports span_mm apart, the force in the middle.
    Stress in the middle: F L / (4 Z). Deflection there: F L³ / (48 E I)."""
    _positive(force_n=force_n, span_mm=span_mm, modulus_gpa=modulus_gpa)
    e = modulus_gpa * 1000
    return Case(
        force_n * span_mm / (4 * section.modulus_mm3),
        force_n * span_mm**3 / (48 * e * section.inertia_mm4),
    )


def tension(
    force_n: float,
    section: Section,
    length_mm: float | None = None,
    modulus_gpa: float | None = None,
) -> Case:
    """A member pulled (or a short one pushed) along its axis: F / A. With its length and
    modulus, how far it stretches: F L / (E A). Buckling of a pushed member is not checked."""
    _positive(force_n=force_n)
    stretch = None
    if length_mm is not None and modulus_gpa is not None:
        _positive(length_mm=length_mm, modulus_gpa=modulus_gpa)
        stretch = force_n * length_mm / (modulus_gpa * 1000 * section.area_mm2)
    return Case(force_n / section.area_mm2, stretch)


# --- screws ---------------------------------------------------------------------------------
# Nominal yield strength by property class (ISO 898-1 for steel, ISO 3506-1 for stainless).
PROPERTY_CLASSES: dict[str, float] = {
    "4.8": 320,
    "8.8": 640,
    "10.9": 900,
    "12.9": 1080,
    "A2-70": 450,
    "A4-70": 450,
    "A2-80": 600,
    "A4-80": 600,
}
SHEAR_RATIO = 1 / math.sqrt(3)  # yield in shear over yield in tension (von Mises): 0.577


def stress_area(thread: str) -> float:
    """The cross-section of a metric coarse thread that carries load, in mm² (ISO 898-1):
    π/4 (d - 0.9382 P)². M8: 36.6."""
    return math.pi / 4 * (fasteners.diameter(thread) - 0.9382 * fasteners.pitch(thread)) ** 2


def screw_yield(property_class: str) -> float:
    try:
        return PROPERTY_CLASSES[property_class]
    except KeyError:
        raise ValueError(
            f"'{property_class}' isn't a known property class: {', '.join(PROPERTY_CLASSES)}"
        ) from None


def screws_in_shear(force_n: float, thread: str, count: int = 1, planes: int = 1) -> Case:
    """Screws loaded across their axis, the force shared equally, sheared through the thread
    (the worse case): F / (count x planes x stress area). Compare with screw_shear_yield().
    A joint is better designed so friction or a dowel takes the shear; this is the fallback."""
    _positive(force_n=force_n, count=count, planes=planes)
    return Case(force_n / (count * planes * stress_area(thread)))


def screw_shear_yield(property_class: str) -> float:
    return SHEAR_RATIO * screw_yield(property_class)


# --- snap fits ------------------------------------------------------------------------------
# Permissible strain in a snap arm that is deflected briefly, once (fraction, not percent).
# Typical design-guide figures, on the careful side; for a joint opened often, use about 60%.
# Printed plastics break far earlier across their layers: lay a snap arm flat in the print.
PERMISSIBLE_STRAIN: dict[str, float] = {
    "PLA": 0.015,
    "PETG": 0.03,
    "ABS": 0.025,
    "ASA": 0.025,
    "PA12": 0.04,
    "PC": 0.04,
    "PP": 0.06,
    "POM": 0.05,
    "Resin, standard": 0.015,
}
REPEATED = 0.6


def snap_arm_strain(deflection_mm: float, length_mm: float, thickness_mm: float) -> float:
    """The strain at the root of a straight snap arm of constant rectangular section, when its
    tip is pushed aside by deflection_mm: 1.5 h y / L²."""
    _positive(deflection_mm=deflection_mm, length_mm=length_mm, thickness_mm=thickness_mm)
    return 1.5 * thickness_mm * deflection_mm / length_mm**2


def snap_arm_force(
    deflection_mm: float, length_mm: float, thickness_mm: float, width_mm: float, modulus_gpa: float
) -> float:
    """The force that pushes the arm's tip aside by deflection_mm: 3 E I y / L³."""
    _positive(width_mm=width_mm, modulus_gpa=modulus_gpa)
    snap_arm_strain(deflection_mm, length_mm, thickness_mm)  # checks the rest
    inertia = width_mm * thickness_mm**3 / 12
    return 3 * modulus_gpa * 1000 * inertia * deflection_mm / length_mm**3


def permissible_strain(
    material: str, yield_mpa: float, modulus_gpa: float, repeated: bool = False
) -> float:
    """What a snap arm of this material may be strained to: the plastics from the table above;
    anything else stays elastic (yield over modulus)."""
    strain = PERMISSIBLE_STRAIN.get(material, yield_mpa / (modulus_gpa * 1000))
    return strain * REPEATED if repeated and material in PERMISSIBLE_STRAIN else strain


def safety_factor(allowable: float, actual: float) -> float:
    """How many times the load the member takes before it reaches what is allowed."""
    return math.inf if actual <= 0 else allowable / actual
