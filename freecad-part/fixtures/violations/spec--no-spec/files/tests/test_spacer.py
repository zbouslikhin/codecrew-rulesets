from parts import spacer


def test_it_is_one_solid() -> None:
    assert len(spacer.build().Solids) == 1
