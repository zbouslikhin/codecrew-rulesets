from fixture_app.lists import append


def test_append() -> None:
    assert append(1, []) == [1]
