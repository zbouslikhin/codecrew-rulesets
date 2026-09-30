from parts.plate import make


def test_plate() -> None:
    assert make().Volume > 0
