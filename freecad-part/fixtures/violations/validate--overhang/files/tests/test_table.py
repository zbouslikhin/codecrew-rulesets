from parts import table


def test_it_is_one_solid() -> None:
    assert len(table.build().Solids) == 1
