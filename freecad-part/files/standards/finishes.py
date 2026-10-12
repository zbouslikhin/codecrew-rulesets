"""Surface finishes: what a part can be finished with, by its material and process.

A spec's finish should be one of these names, so the checks can tell whether it suits the
material. A finish that isn't here can still be named; it just can't be checked.
"""

from __future__ import annotations

from standards import materials

PLASTICS = ("PLA", "PETG", "ABS", "ASA", "PA12", "PC", "PP", "POM", "Resin, standard")


def family(material: str) -> str:
    """plastic, aluminium, steel, stainless or brass."""
    if material in PLASTICS:
        return "plastic"
    for name in ("Aluminium", "Stainless", "Steel", "Brass"):
        if material.startswith(name):
            return name.lower()
    return "other"


METALS = ("aluminium", "steel", "stainless", "brass")
# finish: (the material families it suits, the processes it follows; empty: any)
FINISHES: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    "as printed": (("plastic",), ("fdm", "sla", "sls")),
    "sanded and painted": (("plastic",), ()),
    "vapour smoothed": (("plastic",), ("fdm",)),
    "as moulded, textured": (("plastic",), ("injection_moulding",)),
    "as moulded, polished": (("plastic",), ("injection_moulding",)),
    "as machined": (("plastic", *METALS), ("milling", "turning")),
    "as cut, deburred": (METALS, ("laser_cutting", "sheet_metal")),
    "bead blasted": (METALS, ()),
    "brushed": (METALS, ()),
    "polished": (METALS, ()),
    "anodised": (("aluminium",), ()),
    "hard anodised": (("aluminium",), ()),
    "powder coated": (METALS, ()),
    "zinc plated": (("steel",), ()),
    "black oxide": (("steel",), ()),
    "passivated": (("stainless",), ()),
}
# only these plastics take vapour smoothing
VAPOUR_SMOOTHED = ("ABS", "ASA")


def problem(finish: str, material: str, processes: list[str]) -> str | None:
    """Why this finish doesn't suit this material and these processes; None when it does, or
    when the finish isn't one this library knows."""
    if finish not in FINISHES or materials.get(material) is None:
        return None
    families, after = FINISHES[finish]
    kind = family(material)
    if kind not in families or (finish == "vapour smoothed" and material not in VAPOUR_SMOOTHED):
        suits = ", ".join(VAPOUR_SMOOTHED) if finish == "vapour smoothed" else ", ".join(families)
        return f"'{finish}' is a finish for {suits}, and {material} isn't"
    if after and not any(p in after for p in processes):
        made = ", ".join(processes)
        return f"'{finish}' follows {', '.join(after)}, and this part is made by {made}"
    return None
