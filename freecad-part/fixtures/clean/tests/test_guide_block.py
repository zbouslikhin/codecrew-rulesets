from parts import guide_block


def test_the_bore_goes_through() -> None:
    p = guide_block.PARAMS
    solid = guide_block.build(p)
    assert len(solid.Solids) == 1
    full = p.length_mm * p.width_mm * p.height_mm
    assert solid.Volume < full  # material was removed all the way
