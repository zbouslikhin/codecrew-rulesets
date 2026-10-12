from parts import shell


def test_it_is_one_solid() -> None:
    assert len(shell.build().Solids) == 1
