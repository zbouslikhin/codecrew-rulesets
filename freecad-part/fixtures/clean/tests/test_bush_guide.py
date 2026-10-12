from assemblies import bush_guide


def test_the_bush_sits_in_the_bore() -> None:
    parts = bush_guide.build()
    assert parts["spacer_bush"].common(parts["guide_block"]).Volume < 1e-3
    assert parts["spacer_bush"].distToShape(parts["guide_block"])[0] < 1e-6
