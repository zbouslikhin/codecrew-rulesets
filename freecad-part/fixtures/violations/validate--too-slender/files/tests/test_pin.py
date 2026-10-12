from parts import pin


def test_it_is_one_solid() -> None:
    assert len(pin.build().Solids) == 1
