from parts import panel


def test_it_is_one_solid() -> None:
    assert len(panel.build().Solids) == 1
