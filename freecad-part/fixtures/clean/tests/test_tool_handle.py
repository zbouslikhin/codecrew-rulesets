from parts import tool_handle


def test_it_is_one_solid() -> None:
    assert len(tool_handle.build().Solids) == 1
