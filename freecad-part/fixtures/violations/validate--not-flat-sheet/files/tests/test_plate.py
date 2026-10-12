from parts import plate


def test_it_is_one_solid() -> None:
    assert len(plate.build().Solids) == 1
