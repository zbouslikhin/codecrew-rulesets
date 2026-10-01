import math

from parts.{{name}} import PARAMS, build


def test_outer_dimensions_follow_the_parameters() -> None:
    bb = build().BoundBox
    assert math.isclose(bb.XLength, PARAMS.length_mm)
    assert math.isclose(bb.YLength, PARAMS.width_mm)
    assert math.isclose(bb.ZLength, PARAMS.height_mm)


def test_it_is_one_solid() -> None:
    shape = build()
    assert shape.isValid() and len(shape.Solids) == 1


# TODO: test what matters for this part's function (holes and their fit, clearances, mass).
