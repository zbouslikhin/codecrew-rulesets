from parts import long_rail


def test_it_is_one_solid() -> None:
    assert len(long_rail.build().Solids) == 1
