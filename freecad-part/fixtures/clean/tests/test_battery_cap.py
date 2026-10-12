from parts import battery_cap


def test_it_is_one_solid() -> None:
    assert len(battery_cap.build().Solids) == 1
