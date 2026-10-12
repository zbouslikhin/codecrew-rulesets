from parts import angle


def test_it_is_one_solid() -> None:
    assert len(angle.build().Solids) == 1
