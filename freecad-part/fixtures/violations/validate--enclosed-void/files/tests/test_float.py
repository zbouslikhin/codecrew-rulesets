from parts import float


def test_it_is_one_solid() -> None:
    assert len(float.build().Solids) == 1
