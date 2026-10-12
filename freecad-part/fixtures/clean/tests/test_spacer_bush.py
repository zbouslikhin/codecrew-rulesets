from parts import spacer_bush


def test_it_is_one_solid() -> None:
    assert len(spacer_bush.build().Solids) == 1
