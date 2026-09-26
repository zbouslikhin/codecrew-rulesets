from fixture_app.count import count


def test_count_exists() -> None:
    assert callable(count)
