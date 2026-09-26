from fixture_app.missing import thing


def test_thing() -> None:
    assert thing() == 1
