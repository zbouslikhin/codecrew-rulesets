from parts import tray


def test_it_is_one_solid() -> None:
    assert len(tray.build().Solids) == 1
