"""Metric fasteners: threads, the holes they need, and the standard parts themselves.

Sources: ISO 261/262 (coarse pitch), ISO 273 (clearance holes), ISO 2306 (tap drills),
ISO 4762 (socket head cap screws), DIN 974-1 (counterbores for them), ISO 4032 (hex nuts),
ISO 7089 (plain washers). Lengths in mm.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# thread: (nominal diameter, coarse pitch)
THREADS: dict[str, tuple[float, float]] = {
    "M1.6": (1.6, 0.35),
    "M2": (2.0, 0.4),
    "M2.5": (2.5, 0.45),
    "M3": (3.0, 0.5),
    "M4": (4.0, 0.7),
    "M5": (5.0, 0.8),
    "M6": (6.0, 1.0),
    "M8": (8.0, 1.25),
    "M10": (10.0, 1.5),
    "M12": (12.0, 1.75),
    "M16": (16.0, 2.0),
    "M20": (20.0, 2.5),
}
FITS = ("fine", "medium", "coarse")
# ISO 273: clearance hole diameter, fine / medium / coarse
CLEARANCE: dict[str, tuple[float, float, float]] = {
    "M1.6": (1.7, 1.8, 2.0),
    "M2": (2.2, 2.4, 2.6),
    "M2.5": (2.7, 2.9, 3.1),
    "M3": (3.2, 3.4, 3.6),
    "M4": (4.3, 4.5, 4.8),
    "M5": (5.3, 5.5, 5.8),
    "M6": (6.4, 6.6, 7.0),
    "M8": (8.4, 9.0, 10.0),
    "M10": (10.5, 11.0, 12.0),
    "M12": (13.0, 13.5, 14.5),
    "M16": (17.0, 17.5, 18.5),
    "M20": (21.0, 22.0, 24.0),
}
# ISO 4762 socket head cap screw: head diameter, head height, hex socket size
SOCKET_HEAD: dict[str, tuple[float, float, float]] = {
    "M1.6": (3.0, 1.6, 1.5),
    "M2": (3.8, 2.0, 1.5),
    "M2.5": (4.5, 2.5, 2.0),
    "M3": (5.5, 3.0, 2.5),
    "M4": (7.0, 4.0, 3.0),
    "M5": (8.5, 5.0, 4.0),
    "M6": (10.0, 6.0, 5.0),
    "M8": (13.0, 8.0, 6.0),
    "M10": (16.0, 10.0, 8.0),
    "M12": (18.0, 12.0, 10.0),
    "M16": (24.0, 16.0, 14.0),
    "M20": (30.0, 20.0, 17.0),
}
# DIN 974-1, series 1: counterbore for an ISO 4762 head: diameter, minimum depth
COUNTERBORE: dict[str, tuple[float, float]] = {
    "M3": (6.5, 3.4),
    "M4": (8.0, 4.6),
    "M5": (10.0, 5.7),
    "M6": (11.0, 6.8),
    "M8": (15.0, 9.0),
    "M10": (18.0, 11.0),
    "M12": (20.0, 13.0),
    "M16": (26.0, 17.5),
    "M20": (33.0, 21.5),
}
# ISO 4032 hex nut: width across flats, height
HEX_NUT: dict[str, tuple[float, float]] = {
    "M2": (4.0, 1.6),
    "M2.5": (5.0, 2.0),
    "M3": (5.5, 2.4),
    "M4": (7.0, 3.2),
    "M5": (8.0, 4.7),
    "M6": (10.0, 5.2),
    "M8": (13.0, 6.8),
    "M10": (16.0, 8.4),
    "M12": (18.0, 10.8),
    "M16": (24.0, 14.8),
    "M20": (30.0, 18.0),
}
# ISO 7089 plain washer: inner diameter, outer diameter, thickness
WASHER: dict[str, tuple[float, float, float]] = {
    "M3": (3.2, 7.0, 0.5),
    "M4": (4.3, 9.0, 0.8),
    "M5": (5.3, 10.0, 1.0),
    "M6": (6.4, 12.0, 1.6),
    "M8": (8.4, 16.0, 1.6),
    "M10": (10.5, 20.0, 2.0),
    "M12": (13.0, 24.0, 2.5),
    "M16": (17.0, 30.0, 3.0),
    "M20": (21.0, 37.0, 3.0),
}
# ISO 2306: the drill for a coarse thread before tapping
TAP_DRILL: dict[str, float] = {
    "M1.6": 1.25,
    "M2": 1.6,
    "M2.5": 2.05,
    "M3": 2.5,
    "M4": 3.3,
    "M5": 4.2,
    "M6": 5.0,
    "M8": 6.8,
    "M10": 8.5,
    "M12": 10.2,
    "M16": 14.0,
    "M20": 17.5,
}
# nominal lengths screws are made in
SCREW_LENGTHS = (
    2,
    2.5,
    3,
    4,
    5,
    6,
    8,
    10,
    12,
    16,
    20,
    25,
    30,
    35,
    40,
    45,
    50,
    55,
    60,
    65,
    70,
    80,
    90,
    100,
)
# a screw holds when at least this many diameters of thread are engaged (a rule of thumb:
# more in softer material; a material in standards.materials may say its own)
ENGAGEMENT_DIAMETERS = 1.0


class UnknownThread(KeyError):
    pass


def _row(table: dict[str, tuple], thread: str, what: str) -> tuple:
    try:
        return table[thread]
    except KeyError:
        raise UnknownThread(f"no {what} for {thread}: known are {', '.join(table)}") from None


def diameter(thread: str) -> float:
    """The thread's nominal diameter: 4.0 for M4."""
    return float(_row(THREADS, thread, "thread")[0])


def pitch(thread: str) -> float:
    return float(_row(THREADS, thread, "thread")[1])


def clearance_hole(thread: str, fit: str = "medium") -> float:
    """The hole a screw passes through (ISO 273): fine, medium or coarse."""
    return float(_row(CLEARANCE, thread, "clearance hole")[FITS.index(fit)])


def tap_drill(thread: str) -> float:
    """The hole to drill before tapping (ISO 2306)."""
    try:
        return TAP_DRILL[thread]
    except KeyError:
        raise UnknownThread(
            f"no tap drill for {thread}: known are {', '.join(TAP_DRILL)}"
        ) from None


def counterbore_diameter(thread: str) -> float:
    return float(_row(COUNTERBORE, thread, "counterbore")[0])


def counterbore_depth(thread: str) -> float:
    """The least depth that sinks an ISO 4762 head below the surface."""
    return float(_row(COUNTERBORE, thread, "counterbore")[1])


def head_diameter(thread: str) -> float:
    return float(_row(SOCKET_HEAD, thread, "socket head")[0])


def head_height(thread: str) -> float:
    return float(_row(SOCKET_HEAD, thread, "socket head")[1])


@dataclass(frozen=True)
class StandardPart:
    """A standard part named by its designation, e.g. "ISO 4762 M4x12"."""

    designation: str
    standard: str  # "ISO 4762"
    kind: str  # screw | nut | washer
    thread: str  # "M4"
    length_mm: float | None = None  # screws


KINDS = {"ISO 4762": "screw", "ISO 4032": "nut", "ISO 7089": "washer"}
_DESIGNATION = re.compile(r"^\s*(ISO \d+)\s+(M\d+(?:\.\d+)?)(?:\s*x\s*(\d+(?:\.\d+)?))?\s*$")


def parse(designation: str) -> StandardPart | None:
    """The standard part a designation names, or None when this library doesn't know it."""
    found = _DESIGNATION.match(designation)
    if not found or found.group(1) not in KINDS:
        return None
    standard, thread, length = found.group(1), found.group(2), found.group(3)
    return StandardPart(
        designation.strip(), standard, KINDS[standard], thread, float(length) if length else None
    )


def problems(designation: str) -> list[str]:
    """What's wrong with a designation this library knows the standard of (empty: nothing)."""
    part = parse(designation)
    if part is None:
        return []
    table = {"screw": SOCKET_HEAD, "nut": HEX_NUT, "washer": WASHER}[part.kind]
    if part.thread not in table:
        return [f"{part.standard} has no size {part.thread} here: known are {', '.join(table)}"]
    if part.kind == "screw":
        if part.length_mm is None:
            return [f"a screw's designation ends in its length: {part.standard} {part.thread}x12"]
        if part.length_mm not in SCREW_LENGTHS:
            near = min(SCREW_LENGTHS, key=lambda v: abs(v - part.length_mm))
            return [
                f"{part.length_mm:g} mm isn't a length screws come in: the nearest is {near:g} mm"
            ]
    return []
