from parts import pocket_block


def test_it_is_one_solid() -> None:
    assert len(pocket_block.build().Solids) == 1
