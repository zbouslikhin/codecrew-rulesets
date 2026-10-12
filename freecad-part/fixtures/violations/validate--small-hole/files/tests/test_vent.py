from parts import vent


def test_it_is_one_solid() -> None:
    assert len(vent.build().Solids) == 1
