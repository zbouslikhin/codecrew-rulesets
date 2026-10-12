from parts import slotted_block


def test_it_is_one_solid() -> None:
    assert len(slotted_block.build().Solids) == 1
