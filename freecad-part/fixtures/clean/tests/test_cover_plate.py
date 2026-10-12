from parts import cover_plate


def test_it_is_one_solid() -> None:
    assert len(cover_plate.build().Solids) == 1
