from parts import clamp_block


def test_it_is_one_solid() -> None:
    assert len(clamp_block.build().Solids) == 1
