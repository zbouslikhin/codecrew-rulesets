"""Materials: what a part can be made of, how dense it is, and which processes suit it.

Densities are the usual handbook values. Strength figures are typical ones, for comparing
materials: design to your supplier's datasheet. A project that needs a material that isn't
here asks for it in the ruleset; a spec's material must be one of these names.
"""

from __future__ import annotations

from dataclasses import dataclass

PROCESSES = (
    "fdm",
    "sla",
    "sls",
    "milling",
    "turning",
    "sheet_metal",
    "laser_cutting",
    "injection_moulding",
)


@dataclass(frozen=True)
class Material:
    name: str
    density_g_cm3: float
    yield_mpa: float  # typical yield (metals) or tensile strength (plastics)
    modulus_gpa: float
    processes: tuple[str, ...]
    engagement_diameters: float = 1.0  # thread engagement a screw needs in it, in diameters


_M = Material
MATERIALS: dict[str, Material] = {
    m.name: m
    for m in (
        _M("PLA", 1.24, 50, 3.5, ("fdm",), 2.0),
        _M("PETG", 1.27, 50, 2.1, ("fdm",), 2.0),
        _M("ABS", 1.05, 40, 2.2, ("fdm", "injection_moulding"), 2.0),
        _M("ASA", 1.07, 45, 2.2, ("fdm",), 2.0),
        _M("PA12", 1.01, 48, 1.7, ("fdm", "sls", "injection_moulding"), 2.0),
        _M("PC", 1.20, 60, 2.3, ("fdm", "injection_moulding"), 2.0),
        _M("PP", 0.90, 30, 1.5, ("injection_moulding",), 2.5),
        _M("POM", 1.41, 65, 2.8, ("milling", "turning", "injection_moulding"), 2.0),
        _M("Resin, standard", 1.15, 50, 2.5, ("sla",), 2.0),
        _M(
            "Aluminium 6061-T6",
            2.70,
            275,
            69,
            ("milling", "turning", "sheet_metal", "laser_cutting"),
            1.5,
        ),
        _M("Aluminium 5052-H32", 2.68, 193, 70, ("sheet_metal", "laser_cutting"), 1.5),
        _M("Aluminium 7075-T6", 2.81, 503, 72, ("milling", "turning"), 1.5),
        _M(
            "Steel S235JR",
            7.85,
            235,
            210,
            ("milling", "turning", "sheet_metal", "laser_cutting"),
            1.0,
        ),
        _M(
            "Steel S355J2",
            7.85,
            355,
            210,
            ("milling", "turning", "sheet_metal", "laser_cutting"),
            1.0,
        ),
        _M(
            "Stainless 1.4301 (304)",
            8.00,
            215,
            193,
            ("milling", "turning", "sheet_metal", "laser_cutting"),
            1.0,
        ),
        _M(
            "Stainless 1.4404 (316L)",
            8.00,
            200,
            193,
            ("milling", "turning", "sheet_metal", "laser_cutting"),
            1.0,
        ),
        _M("Brass CW614N", 8.47, 250, 97, ("milling", "turning"), 1.0),
    )
}


def get(name: str) -> Material | None:
    return MATERIALS.get(name)
