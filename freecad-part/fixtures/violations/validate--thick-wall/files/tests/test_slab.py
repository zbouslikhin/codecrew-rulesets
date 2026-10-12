from parts import slab


def test_it_is_one_solid() -> None:
    assert len(slab.build().Solids) == 1
