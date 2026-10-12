from assemblies import sensor_mount

EPS = 1e-6


def test_the_bracket_sits_on_the_frame() -> None:
    parts = sensor_mount.build()
    assert parts["mounting_bracket"].distToShape(parts["frame"])[0] < EPS


def test_nothing_occupies_the_same_space() -> None:
    parts = sensor_mount.build()
    assert parts["mounting_bracket"].common(parts["frame"]).Volume < 1e-3


def test_two_screws_reach_into_the_rail() -> None:
    parts = sensor_mount.build()
    screws = [shape for name, shape in parts.items() if name.startswith("standard:")]
    assert len(screws) == 2
    for screw in screws:
        assert screw.common(parts["frame"]).Volume > 0  # in the tapped hole
        assert screw.common(parts["mounting_bracket"]).Volume < 1e-3  # free in the clearance hole


def test_the_holes_line_up() -> None:
    parts = sensor_mount.build()
    bracket = sensor_mount.hole_centres(parts["mounting_bracket"])
    frame = sensor_mount.hole_centres(parts["frame"])
    assert len(bracket) == len(frame) == 2
    for a, b in zip(bracket, frame, strict=True):
        assert a.distanceToPoint(b) < EPS
