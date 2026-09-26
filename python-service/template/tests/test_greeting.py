from {{module}} import greet


def test_greets_by_name() -> None:
    assert greet("Qlayers") == "Hello, Qlayers!"
