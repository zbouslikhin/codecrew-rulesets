from parts import housing


def test_it_is_one_solid() -> None:
    assert len(housing.build().Solids) == 1
