from parts import block


def test_it_is_one_solid() -> None:
    assert len(block.build().Solids) == 1
