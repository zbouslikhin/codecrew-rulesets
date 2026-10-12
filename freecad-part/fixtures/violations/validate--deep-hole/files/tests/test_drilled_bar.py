from parts import drilled_bar


def test_it_is_one_solid() -> None:
    assert len(drilled_bar.build().Solids) == 1
