import math

from parts.snap_latch import PARAMS, build


def test_it_is_one_solid() -> None:
    shape = build()
    assert shape.isValid() and len(shape.Solids) == 1


def test_the_hook_stands_proud_by_its_depth() -> None:
    bb = build().BoundBox
    assert math.isclose(bb.XLength, PARAMS.base_length_mm)
    assert math.isclose(bb.ZLength, PARAMS.width_mm)
    area = PARAMS.hook_depth_mm * (PARAMS.hook_land_mm + PARAMS.hook_ramp_mm / 2)
    arm = PARAMS.arm_thickness_mm * (
        PARAMS.arm_length_mm + PARAMS.hook_land_mm + PARAMS.hook_ramp_mm
    )
    base = PARAMS.base_length_mm * PARAMS.base_height_mm
    assert math.isclose(build().Volume, (area + arm + base) * PARAMS.width_mm, rel_tol=1e-6)
