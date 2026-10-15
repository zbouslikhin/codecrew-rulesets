"""Tolerances and fits: ISO 286 tolerance classes, ISO 2768 general tolerances.

A dimension's tolerance says how far the made part may differ from the number. A fit is a hole
and a shaft toleranced so they go together as intended: with clearance, tightly, or pressed.
This module turns a class like "H7" or "g6" into limits for a size, in mm.

Covered: sizes up to 500 mm; grades IT5 to IT14; holes H, G, F, E, D, JS; shafts h, g, f, e,
d, js, k (grades 5 to 7), m, n, p. That is the hole-basis system: the hole is an H, and the
shaft's class sets the fit. Other classes exist in the standard; they aren't in this table.
"""

from __future__ import annotations

import re

# upper ends of the size ranges, mm (a size belongs to the first range it doesn't exceed)
RANGES = (3, 6, 10, 18, 30, 50, 80, 120, 180, 250, 315, 400, 500)
# ISO 286-1 standard tolerance grades, micrometres, per range
IT: dict[int, tuple[int, ...]] = {
    5: (4, 5, 6, 8, 9, 11, 13, 15, 18, 20, 23, 25, 27),
    6: (6, 8, 9, 11, 13, 16, 19, 22, 25, 29, 32, 36, 40),
    7: (10, 12, 15, 18, 21, 25, 30, 35, 40, 46, 52, 57, 63),
    8: (14, 18, 22, 27, 33, 39, 46, 54, 63, 72, 81, 89, 97),
    9: (25, 30, 36, 43, 52, 62, 74, 87, 100, 115, 130, 140, 155),
    10: (40, 48, 58, 70, 84, 100, 120, 140, 160, 185, 210, 230, 250),
    11: (60, 75, 90, 110, 130, 160, 190, 220, 250, 290, 320, 360, 400),
    12: (100, 120, 150, 180, 210, 250, 300, 350, 400, 460, 520, 570, 630),
    13: (140, 180, 220, 270, 330, 390, 460, 540, 630, 720, 810, 890, 970),
    14: (250, 300, 360, 430, 520, 620, 740, 870, 1000, 1150, 1300, 1400, 1550),
}
# fundamental deviations of shafts, micrometres, per range.
# d to h: the upper deviation (the shaft is at most this much over nominal)
SHAFT_UPPER: dict[str, tuple[int, ...]] = {
    "d": (-20, -30, -40, -50, -65, -80, -100, -120, -145, -170, -190, -210, -230),
    "e": (-14, -20, -25, -32, -40, -50, -60, -72, -85, -100, -110, -125, -135),
    "f": (-6, -10, -13, -16, -20, -25, -30, -36, -43, -50, -56, -62, -68),
    "g": (-2, -4, -5, -6, -7, -9, -10, -12, -14, -15, -17, -18, -20),
    "h": (0,) * 13,
}
# k to p: the lower deviation (the shaft is at least this much over nominal)
SHAFT_LOWER: dict[str, tuple[int, ...]] = {
    "k": (0, 1, 1, 1, 2, 2, 2, 3, 3, 4, 4, 4, 5),
    "m": (2, 4, 6, 7, 8, 9, 11, 13, 15, 17, 20, 21, 23),
    "n": (4, 8, 10, 12, 15, 17, 20, 23, 27, 31, 34, 37, 40),
    "p": (6, 12, 15, 18, 22, 26, 32, 37, 43, 50, 56, 62, 68),
}
# ISO 2768-1 general tolerances for lengths: +/- mm, for sizes up to 3, 6, 30, 120, 400, 1000
GENERAL_RANGES = (3, 6, 30, 120, 400, 1000)
GENERAL: dict[str, tuple[float | None, ...]] = {
    "f": (0.05, 0.05, 0.1, 0.15, 0.2, 0.3),
    "m": (0.1, 0.1, 0.2, 0.3, 0.5, 0.8),
    "c": (0.2, 0.3, 0.5, 0.8, 1.2, 2.0),
    "v": (None, 0.5, 1.0, 1.5, 2.5, 4.0),
}
# ISO 273: the tolerance class of a clearance hole, by its series
CLEARANCE_HOLE = {"fine": "H12", "medium": "H13", "coarse": "H14"}
_CLASS = re.compile(r"^(JS|js|[A-Za-z])(\d{1,2})$")


class UnknownClass(ValueError):
    pass


def _range(size_mm: float) -> int:
    if not 0 < size_mm <= RANGES[-1]:
        raise UnknownClass(
            f"tolerance classes cover sizes up to {RANGES[-1]} mm, not {size_mm:g} mm"
        )
    return next(i for i, top in enumerate(RANGES) if size_mm <= top)


def grade_mm(grade: int, size_mm: float) -> float:
    """The width of tolerance grade IT<grade> at a size: IT7 at 20 mm is 0.021."""
    if grade not in IT:
        raise UnknownClass(f"grade IT{grade} isn't in the table (IT{min(IT)} to IT{max(IT)})")
    return IT[grade][_range(size_mm)] / 1000


def limits(tolerance_class: str, size_mm: float) -> tuple[float, float]:
    """(lower, upper) deviation in mm of a class at a size: H7 at 20 is (0.0, 0.021), g6 at 20
    is (-0.020, -0.007)."""
    found = _CLASS.match(tolerance_class.strip())
    if not found:
        raise UnknownClass(
            f"'{tolerance_class}' isn't a tolerance class: a letter and a grade, like H7 or g6"
        )
    letter, grade = found.group(1), int(found.group(2))
    width = grade_mm(grade, size_mm)
    i = _range(size_mm)
    if letter in ("JS", "js"):
        return -width / 2, width / 2
    if letter.isupper():  # a hole: the mirror of the shaft of the same letter
        low = letter.lower()
        if low not in SHAFT_UPPER:
            raise UnknownClass(
                f"hole class {letter} isn't in the table: holes are H, G, F, E, D or JS "
                "(use an H hole and set the fit with the shaft)"
            )
        lower = -SHAFT_UPPER[low][i] / 1000
        return lower, lower + width
    if letter in SHAFT_UPPER:
        upper = SHAFT_UPPER[letter][i] / 1000
        return upper - width, upper
    if letter in SHAFT_LOWER:
        if letter == "k" and not 5 <= grade <= 7:
            raise UnknownClass("shaft class k is in the table for grades 5 to 7")
        lower = SHAFT_LOWER[letter][i] / 1000
        return lower, lower + width
    raise UnknownClass(
        f"shaft class {letter} isn't in the table: shafts are d, e, f, g, h, js, k, m, n or p"
    )


def general(tolerance_class: str, size_mm: float) -> float:
    """The +/- of an ISO 2768-1 general tolerance (f, m, c or v) at a size."""
    if tolerance_class not in GENERAL:
        raise UnknownClass(
            f"general tolerance is f, m, c or v (ISO 2768-1), not '{tolerance_class}'"
        )
    if not 0 < size_mm <= GENERAL_RANGES[-1]:
        raise UnknownClass(f"general tolerances cover sizes up to {GENERAL_RANGES[-1]} mm")
    value = GENERAL[tolerance_class][
        next(i for i, top in enumerate(GENERAL_RANGES) if size_mm <= top)
    ]
    if value is None:
        raise UnknownClass(f"class {tolerance_class} has no value below 3 mm")
    return value


def grade_of(band_mm: float, size_mm: float) -> int | None:
    """The finest grade whose width is at most this band at this size: how demanding a
    tolerance is. None: looser than IT14."""
    i = _range(size_mm)
    return next((g for g in sorted(IT, reverse=True) if IT[g][i] / 1000 <= band_mm + 1e-9), None)


def fit(hole: tuple[float, float], shaft: tuple[float, float]) -> tuple[float, float, str]:
    """A hole and a shaft, each as (smallest, largest) size: (least clearance, most clearance,
    the kind of fit). A negative clearance is an interference."""
    least, most = hole[0] - shaft[1], hole[1] - shaft[0]
    kind = "clearance" if least >= 0 else "interference" if most <= 0 else "transition"
    return least, most, kind
