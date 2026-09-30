import math

import Part

from parts.mounting_bracket import DENSITY_G_CM3, PARAMS, build


def test_outer_dimensions_follow_the_parameters() -> None:
    bb = build().BoundBox
    assert math.isclose(bb.XLength, PARAMS.width_mm)
    assert math.isclose(bb.YLength, PARAMS.depth_mm)
    assert math.isclose(bb.ZLength, PARAMS.height_mm)


def test_two_m4_clearance_holes() -> None:
    radius = PARAMS.hole_diameter_mm / 2
    holes = [
        f
        for f in build().Faces
        if isinstance(f.Surface, Part.Cylinder) and math.isclose(f.Surface.Radius, radius)
    ]
    assert len(holes) == 2


def test_it_is_one_printable_solid() -> None:
    shape = build()
    assert shape.isValid() and len(shape.Solids) == 1
    assert PARAMS.thickness_mm >= 2.0  # thinner walls don't print solid


def test_mass_is_plausible() -> None:
    grams = build().Volume / 1000 * DENSITY_G_CM3
    assert 5 < grams < 20


def _widths(extra: list[float] = []) -> list[float]:
    return [40.0, *extra]
