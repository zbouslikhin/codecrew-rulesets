"""Standard sizes: what stock, tools and tables come in, so a dimension can be bought or cut.

A spec says which parameter follows which standard ([[standards]]); the checks compare the
part's value with what this module allows, and name the nearest standard values when it isn't.
"""

from __future__ import annotations

from standards import fasteners

# ISO 3 preferred numbers, one decade (R20 contains R10)
R20 = (
    1.0,
    1.12,
    1.25,
    1.4,
    1.6,
    1.8,
    2.0,
    2.24,
    2.5,
    2.8,
    3.15,
    3.55,
    4.0,
    4.5,
    5.0,
    5.6,
    6.3,
    7.1,
    8.0,
    9.0,
)
# sheet and plate thicknesses commonly stocked, mm
SHEET = (0.5, 0.8, 1.0, 1.2, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 8.0, 10.0, 12.0, 15.0, 20.0)
# DIN 250 radii, mm
RADII = (
    0.2,
    0.3,
    0.4,
    0.5,
    0.6,
    0.8,
    1.0,
    1.2,
    1.6,
    2.0,
    2.5,
    3.0,
    4.0,
    5.0,
    6.0,
    8.0,
    10.0,
    12.0,
    16.0,
    20.0,
    25.0,
)

KINDS = {
    "clearance_hole": "a clearance hole for a screw (ISO 273); needs thread, optionally fit",
    "tap_drill": "the hole drilled before tapping (ISO 2306); needs thread",
    "counterbore_diameter": "the counterbore for a socket head (DIN 974-1); needs thread",
    "counterbore_depth": "at least the depth that sinks a socket head (DIN 974-1); needs thread",
    "sheet_thickness": "a stocked sheet or plate thickness",
    "radius": "a standard radius (DIN 250)",
    "drill": "a drilled hole: 0.1 mm steps up to 10 mm, 0.5 mm steps above",
    "preferred": "a preferred number (ISO 3, R20 series)",
}
NEEDS_THREAD = ("clearance_hole", "tap_drill", "counterbore_diameter", "counterbore_depth")
EPS = 1e-6


def _preferred(value: float) -> bool:
    if value <= 0:
        return False
    decade = value
    while decade >= 10 - EPS:
        decade /= 10
    while decade < 1 - EPS:
        decade *= 10
    return any(abs(decade - r) < 1e-4 * max(1.0, r) for r in (*R20, 10.0))


def _drill(value: float) -> bool:
    step = 0.1 if value <= 10 + EPS else 0.5
    return value > 0 and abs(round(value / step) * step - value) < EPS


def check(kind: str, value: float, thread: str | None = None, fit: str | None = None) -> str | None:
    """None when `value` follows the standard; otherwise what the standard allows, in words."""
    if kind == "clearance_hole":
        allowed = fasteners.CLEARANCE[thread or ""]
        wanted = [allowed[fasteners.FITS.index(fit)]] if fit else list(allowed)
        if any(abs(value - w) < EPS for w in wanted):
            return None
        pairs = zip(allowed, fasteners.FITS, strict=True)
        said = ", ".join(f"{v:g} ({f})" for v, f in pairs if not fit or f == fit)
        return f"a clearance hole for {thread} is {said} mm (ISO 273)"
    if kind == "tap_drill":
        want = fasteners.tap_drill(thread or "")
        return (
            None
            if abs(value - want) < EPS
            else f"the tap drill for {thread} is {want:g} mm (ISO 2306)"
        )
    if kind == "counterbore_diameter":
        want = fasteners.counterbore_diameter(thread or "")
        if abs(value - want) < EPS:
            return None
        return f"the counterbore for an {thread} socket head is {want:g} mm (DIN 974-1)"
    if kind == "counterbore_depth":
        want = fasteners.counterbore_depth(thread or "")
        if value >= want - EPS:
            return None
        return f"an {thread} socket head needs a counterbore at least {want:g} mm deep (DIN 974-1)"
    if kind in ("sheet_thickness", "radius"):
        table = SHEET if kind == "sheet_thickness" else RADII
        if any(abs(value - t) < EPS for t in table):
            return None
        below = max((t for t in table if t < value), default=None)
        above = min((t for t in table if t > value), default=None)
        near = " or ".join(f"{t:g}" for t in (below, above) if t is not None)
        what = "stocked thicknesses" if kind == "sheet_thickness" else "standard radii (DIN 250)"
        return f"the nearest {what} are {near} mm"
    if kind == "drill":
        return (
            None
            if _drill(value)
            else "drills come in 0.1 mm steps up to 10 mm and 0.5 mm steps above"
        )
    if kind == "preferred":
        if _preferred(value):
            return None
        series = ", ".join(f"{r:g}" for r in R20)
        return f"preferred numbers (ISO 3, R20) are {series} and their decades"
    raise KeyError(kind)
