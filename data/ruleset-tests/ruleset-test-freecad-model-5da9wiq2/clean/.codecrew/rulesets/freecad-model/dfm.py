"""Design for manufacturing: measurements on the built solid, judged by a process profile.

The measurements are the same for every process; a profile (processes.toml, and the project's
own design/processes.toml) says which apply and with what limits. So a new process is a
profile, not code.

Measured: wall thickness (rays through the material from every face), holes (diameter, depth,
blind or through), internal corners (sharp, or their radius), overhangs and bridges against a
build direction, draft and undercuts against a pull direction, reach from tool directions,
enclosed voids, rotational symmetry, flat-sheet form, and overall size.

These are geometric rules of thumb, the kind a manufacturer's design guide gives. They catch
what can't be made; they don't replace talking to whoever makes the part.
"""

from __future__ import annotations

import math
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

import FreeCAD as App  # must come before Part
import Part

EPS = 1e-6
STEP = 0.01  # how far a probe point is moved off a surface, mm
GRID = 3  # sample points per face and direction
AXES = {"+x": (1, 0, 0), "-x": (-1, 0, 0), "+y": (0, 1, 0), "-y": (0, -1, 0), "+z": (0, 0, 1), "-z": (0, 0, -1)}


@dataclass
class Finding:
    code: str
    message: str


@dataclass
class Sample:
    point: App.Vector
    normal: App.Vector  # pointing out of the material
    face: int


@dataclass
class Hole:
    diameter: float
    depth: float
    axis: App.Vector
    centre: App.Vector
    through: bool


@dataclass
class Fillet:
    """A concave cylindrical face that isn't a full hole: an internal corner's radius."""

    radius: float
    height: float
    axis: App.Vector
    centre: App.Vector


@dataclass
class Measured:
    shape: Part.Shape
    samples: list[Sample] = field(default_factory=list)
    holes: list[Hole] = field(default_factory=list)
    fillets: list[Fillet] = field(default_factory=list)
    reach: float = 0.0  # longer than anything in the part


def vec(direction: str) -> App.Vector:
    return App.Vector(*AXES[direction])


def where(p: App.Vector) -> str:
    return f"x {p.x:.1f}, y {p.y:.1f}, z {p.z:.1f}"


def inside(shape: Part.Shape, p: App.Vector) -> bool:
    return bool(shape.isInside(p, 1e-7, False))


def measure(shape: Part.Shape) -> Measured:
    m = Measured(shape, reach=shape.BoundBox.DiagonalLength * 1.5 + 1)
    groups: dict[tuple, list] = {}
    for index, face in enumerate(shape.Faces):
        u0, u1, v0, v1 = face.ParameterRange
        for i in range(1, GRID + 1):
            for j in range(1, GRID + 1):
                u = u0 + (u1 - u0) * i / (GRID + 1)
                v = v0 + (v1 - v0) * j / (GRID + 1)
                try:
                    p = face.valueAt(u, v)
                    if not face.isInside(p, 1e-6, True):
                        continue  # outside the trimmed face
                    n = face.normalAt(u, v)
                except Exception:  # noqa: BLE001  (a degenerate patch)
                    continue
                if n.Length < EPS:
                    continue
                n.normalize()
                if inside(shape, p + n * STEP):  # make it point out of the material
                    n = n * -1
                m.samples.append(Sample(p, n, index))
        surface = face.Surface
        if isinstance(surface, Part.Cylinder):
            mine = [s for s in m.samples if s.face == index]
            if not mine:
                continue
            s = mine[0]
            axis = App.Vector(surface.Axis)
            foot = surface.Center + axis * (s.point - surface.Center).dot(axis)
            if (s.point + s.normal * STEP - foot).Length < (s.point - foot).Length:  # concave
                if axis.x < -EPS or (abs(axis.x) < EPS and (axis.y < -EPS or (abs(axis.y) < EPS and axis.z < 0))):
                    axis = axis * -1
                base = surface.Center - axis * surface.Center.dot(axis)  # the axis, independent of where
                key = (round(surface.Radius, 4), *(round(c, 3) for c in (*axis, *base)))
                groups.setdefault(key, []).append(face)
    for key, faces in groups.items():
        radius = key[0]
        axis = App.Vector(*key[1:4])
        base = App.Vector(*key[4:7])
        span = sum(f.ParameterRange[1] - f.ParameterRange[0] for f in faces)
        along = [v.Point.dot(axis) for f in faces for v in f.Vertexes]
        low, high = min(along), max(along)
        centre = base + axis * ((low + high) / 2)
        if span >= 2 * math.pi - 1e-3:
            # blind when material closes an end
            closed = [inside(shape, base + axis * (t + sign * STEP)) for t, sign in ((low, -1), (high, 1))]
            m.holes.append(Hole(2 * radius, high - low, axis, centre, not any(closed)))
        else:
            m.fillets.append(Fillet(radius, high - low, axis, centre))
    return m


def ray_blocked(m: Measured, p: App.Vector, direction: App.Vector, normal: App.Vector) -> bool:
    """Whether material lies between a surface point and the open, going in `direction`. The
    ray starts just off the surface, so one that runs along a wall isn't taken for blocked."""
    start = p + normal * STEP + direction * STEP
    line = Part.makeLine(start, start + direction * m.reach)
    try:
        hit = line.common(m.shape)
    except Exception:  # noqa: BLE001
        return False
    return any(e.Length > STEP for e in hit.Edges)


def thickness(m: Measured, s: Sample) -> float | None:
    """How much material lies behind a surface point, straight through."""
    start = s.point - s.normal * (STEP / 10)
    line = Part.makeLine(start, start - s.normal * m.reach)
    try:
        hit = line.common(m.shape)
    except Exception:  # noqa: BLE001
        return None
    pieces = sorted(hit.Edges, key=lambda e: min((v.Point - start).Length for v in e.Vertexes))
    return pieces[0].Length + STEP / 10 if pieces else None


# --- the rules: each reads its limits from the profile ------------------------------
def walls(m: Measured, profile: dict, out: list[Finding]) -> None:
    least, most = profile.get("min_wall_mm"), profile.get("max_wall_mm")
    if least is None and most is None:
        return
    found = [(t, s) for s in m.samples if (t := thickness(m, s)) is not None and t > STEP]
    if not found:
        return
    thin = min(found, key=lambda f: f[0])
    if least is not None and thin[0] < least - 1e-4:
        out.append(Finding("thin-wall", f"a wall is {thin[0]:.2f} mm thick at {where(thin[1].point)}; "
                                        f"at least {least:g} mm"))
    if most is not None:
        # a wall is as thick as its thinner side lets it be: judge the local minimum per face
        per_face: dict[int, float] = {}
        for t, s in found:
            if isinstance(m.shape.Faces[s.face].Surface, Part.Plane):  # a hole's wall is measured along the wall
                per_face[s.face] = min(per_face.get(s.face, t), t)
        if not per_face:
            return
        thick = max(per_face.values())
        if thick > most + 1e-4:
            face = max(per_face, key=lambda k: per_face[k])
            at = next(s for _, s in found if s.face == face)
            out.append(Finding("thick-wall", f"a section is {thick:.2f} mm thick at {where(at.point)}; at most "
                                             f"{most:g} mm, or it sinks and warps: core it out"))


def holes(m: Measured, profile: dict, out: list[Finding], t: float | None = None) -> None:
    least = profile.get("min_hole_mm")
    if profile.get("min_hole_factor") is not None and t:
        least = max(least or 0.0, profile["min_hole_factor"] * t)
    ratio = profile.get("max_hole_depth_ratio")
    for h in m.holes:
        if least is not None and h.diameter < least - 1e-4:
            out.append(Finding("small-hole", f"a hole is {h.diameter:.2f} mm in diameter at {where(h.centre)}; "
                                             f"at least {least:g} mm"))
        if ratio is not None and h.depth / h.diameter > ratio + 1e-4:
            out.append(Finding("deep-hole", f"a {h.diameter:.2f} mm hole is {h.depth:.1f} mm deep at "
                                            f"{where(h.centre)}: {h.depth / h.diameter:.1f} times its diameter, "
                                            f"at most {ratio:g}"))


def overhangs(m: Measured, profile: dict, up: App.Vector, out: list[Finding]) -> None:
    limit = profile.get("max_overhang_deg")
    if limit is None:
        return
    bed = min(v.Point.dot(up) for v in m.shape.Vertexes)
    bridge = profile.get("max_bridge_mm", 0.0)
    round_ok = profile.get("max_unsupported_hole_mm", 0.0)
    steep = -math.cos(math.radians(limit)) - 1e-6
    for h in m.holes:
        if abs(h.axis.dot(up)) < 0.1 and h.diameter > round_ok + 1e-6:
            out.append(Finding("overhang", f"a {h.diameter:.1f} mm hole lies on its side at {where(h.centre)}: its "
                                           f"crown overhangs. Up to {round_ok:g} mm prints unsupported; make it a "
                                           "teardrop, or turn the part"))
    flagged: dict[int, Sample] = {}
    for s in m.samples:
        if isinstance(m.shape.Faces[s.face].Surface, Part.Cylinder) and any(
            abs(h.axis.dot(up)) < 0.1 and abs(2 * m.shape.Faces[s.face].Surface.Radius - h.diameter) < 1e-4
            for h in m.holes
        ):
            continue  # a hole on its side: judged above, by its size
        if s.normal.dot(up) >= steep or s.point.dot(up) < bed + 1e-4:
            continue  # not facing down steeply, or lying on the bed
        face = m.shape.Faces[s.face]
        if s.normal.dot(up) < -1 + 1e-6 and bridge:
            box = face.BoundBox
            spans = sorted(d for d in (box.XLength, box.YLength, box.ZLength) if d > 1e-6)
            if spans and spans[0] <= bridge + 1e-6:
                continue  # a flat underside short enough to bridge
        flagged.setdefault(s.face, s)
    for index, s in flagged.items():
        area = m.shape.Faces[index].Area
        out.append(Finding("overhang", f"a surface of {area:.0f} mm² at {where(s.point)} overhangs more than "
                                       f"{limit:g}° from vertical and needs support: turn the part, chamfer it, "
                                       "or split it"))


def sharp_internal_edges(m: Measured) -> list[tuple[App.Vector, list[App.Vector]]]:
    """Edges where two faces meet in an internal corner with no radius: (a point on the edge,
    the two faces' outward normals there)."""
    found = []
    for edge in m.shape.Edges:
        faces = m.shape.ancestorsOfType(edge, Part.Face)
        if len(faces) != 2:
            continue
        param = (edge.FirstParameter + edge.LastParameter) / 2
        mid = edge.valueAt(param)
        normals = []
        for face in faces:
            try:
                u, v = face.Surface.parameter(mid)
                n = face.normalAt(u, v)
            except Exception:  # noqa: BLE001
                break
            n.normalize()
            if inside(m.shape, mid + n * STEP):
                n = n * -1
            normals.append(n)
        if len(normals) != 2 or normals[0].cross(normals[1]).Length < 0.02:
            continue  # smooth: no corner
        # the direction in which the first face leaves the edge: towards the second face's
        # outside means the corner is internal
        tangent = edge.tangentAt(param)
        away = normals[0].cross(tangent)
        if away.Length < EPS:
            continue
        away.normalize()
        if not faces[0].isInside(mid + away * (STEP * 5), 1e-3, True):
            away = away * -1
        if away.dot(normals[1]) > 0.02:
            found.append((mid, normals))
    return found


def corners(m: Measured, profile: dict, tools: list[App.Vector], out: list[Finding]) -> None:
    least = profile.get("min_internal_radius_mm")
    deep = profile.get("max_corner_depth_ratio")
    if least is None:
        return
    for f in m.fillets:
        if not any(abs(f.axis.dot(d)) > 0.999 for d in tools):
            continue
        if f.radius < least - 1e-4:
            out.append(Finding("tight-internal-corner", f"an internal corner has a {f.radius:.2f} mm radius at "
                                                        f"{where(f.centre)}; at least {least:g} mm, the cutter's"))
        elif deep is not None and f.height / (2 * f.radius) > deep + 1e-4:
            out.append(Finding("deep-corner", f"an internal corner of radius {f.radius:.2f} mm is {f.height:.1f} mm "
                                              f"deep at {where(f.centre)}: the cutter would be "
                                              f"{f.height / (2 * f.radius):.1f} diameters long, at most {deep:g}"))
    for mid, normals in sharp_internal_edges(m):
        # a floor meeting a wall is what an end mill leaves; two walls meeting sharply is not
        if any(abs(n.dot(d)) > 0.999 for n in normals for d in tools):
            continue
        out.append(Finding("sharp-internal-corner", f"a sharp internal corner at {where(mid)}: a rotating cutter "
                                                    f"leaves a radius there; give it at least {least:g} mm"))


def draft(m: Measured, profile: dict, up: App.Vector, out: list[Finding]) -> None:
    least = profile.get("min_draft_deg")
    if least is None:
        return
    free = profile.get("draft_free_height_mm", 0.5)
    flat = math.sin(math.radians(least)) - 1e-6
    seen: set[int] = set()
    for s in m.samples:
        if s.face in seen or abs(s.normal.dot(up)) >= flat:
            continue
        face = m.shape.Faces[s.face]
        heights = [v.Point.dot(up) for v in face.Vertexes]
        if heights and max(heights) - min(heights) <= free:
            continue
        seen.add(s.face)
        out.append(Finding("no-draft", f"a face at {where(s.point)} runs along the direction of pull with less "
                                       f"than {least:g}° of draft: it drags on the mould when the part is ejected"))


def reachable(m: Measured, directions: list[App.Vector], code: str, what: str, out: list[Finding]) -> None:
    seen: set[int] = set()
    for s in m.samples:
        if s.face in seen:
            continue
        open_from = [d for d in directions if s.normal.dot(d) > -0.02]
        if any(not ray_blocked(m, s.point, d, s.normal) for d in open_from):
            continue
        seen.add(s.face)
        out.append(Finding(code, f"the surface at {where(s.point)} {what}"))


def voids(m: Measured, profile: dict, out: list[Finding]) -> None:
    if profile.get("enclosed_voids", True):
        return
    if any(len(solid.Shells) > 1 for solid in m.shape.Solids):
        out.append(Finding("enclosed-void", "the part has a closed cavity inside: nothing can get in to make it, "
                                            "or out of it afterwards. Open it up"))


def rotational(m: Measured, profile: dict, out: list[Finding]) -> None:
    if not profile.get("rotational"):
        return
    box = m.shape.BoundBox
    best = None
    for name in ("+x", "+y", "+z"):
        axis = vec(name)
        turned = m.shape.copy()
        turned.rotate(m.shape.BoundBox.Center, axis, 37.0)
        try:
            same = turned.common(m.shape).Volume
        except Exception:  # noqa: BLE001
            continue
        if abs(same - m.shape.Volume) <= 1e-3 * m.shape.Volume:
            best = axis
            break
    if best is None:
        out.append(Finding("not-rotational", "the part isn't a body of revolution: turning makes round parts. "
                                             "Features off the axis need another process"))
        return
    length = abs(App.Vector(box.XLength, box.YLength, box.ZLength).dot(best))
    across = max(d for d, a in zip((box.XLength, box.YLength, box.ZLength), best, strict=True) if abs(a) < 0.5)
    slender = profile.get("max_length_to_diameter")
    if slender is not None and length / across > slender + 1e-6:
        out.append(Finding("too-slender", f"the part is {length:.1f} mm long and {across:.1f} mm across: "
                                          f"{length / across:.1f} to 1, at most {slender:g} without support"))


def flat_sheet(m: Measured, profile: dict, out: list[Finding]) -> float | None:
    """For processes that cut a flat sheet: the part is a constant-thickness plate with its
    cut faces square to it. Returns the sheet's thickness."""
    if not profile.get("flat_sheet"):
        return None
    box = m.shape.BoundBox
    sizes = {"+x": box.XLength, "+y": box.YLength, "+z": box.ZLength}
    name = min(sizes, key=lambda k: sizes[k])
    normal, t = vec(name), sizes[name]
    for s in m.samples:
        along = abs(s.normal.dot(normal))
        if 0.02 < along < 0.999:
            out.append(Finding("not-flat-sheet", f"the surface at {where(s.point)} is neither the sheet's face nor "
                                                 "a cut square to it: a flat sheet is cut straight through"))
            return t
    faces = [s for s in m.samples if abs(s.normal.dot(normal)) >= 0.999]
    low, high = min(v.Point.dot(normal) for v in m.shape.Vertexes), max(v.Point.dot(normal) for v in m.shape.Vertexes)
    if any(min(abs(s.point.dot(normal) - low), abs(s.point.dot(normal) - high)) > 1e-4 for s in faces):
        out.append(Finding("not-flat-sheet", "the part has steps in its thickness: a sheet has one thickness. "
                                             "Pockets and counterbores need another process"))
    return t


def bends(m: Measured, profile: dict, out: list[Finding]) -> None:
    factor = profile.get("min_bend_radius_factor")
    if factor is None:
        return
    found = [t for s in m.samples if (t := thickness(m, s)) is not None and t > STEP]
    if not found:
        return
    t = min(found)
    for mid, _ in sharp_internal_edges(m):
        out.append(Finding("tight-bend", f"a bend at {where(mid)} has no inside radius: sheet can't be folded "
                                         f"sharp. Give it at least {factor:g} times the {t:.2f} mm thickness"))
    for f in m.fillets:
        if f.radius < factor * t - 1e-4:
            out.append(Finding("tight-bend", f"a bend has an inside radius of {f.radius:.2f} mm at {where(f.centre)}; "
                                             f"at least {factor:g} times the {t:.2f} mm thickness, or it cracks"))


def size(m: Measured, profile: dict, out: list[Finding]) -> None:
    room = profile.get("max_size_mm")
    if not isinstance(room, list) or len(room) != 3:
        return
    try:
        box = m.shape.optimalBoundingBox(False, False)  # the quick one is loose on rounded surfaces
    except Exception:  # noqa: BLE001
        box = m.shape.BoundBox
    have = sorted((box.XLength, box.YLength, box.ZLength))
    if any(h > r + 1e-6 for h, r in zip(have, sorted(room), strict=True)):
        out.append(Finding("too-large", f"the part is {box.XLength:.0f} x {box.YLength:.0f} x {box.ZLength:.0f} mm; "
                                        f"the process takes {room[0]:g} x {room[1]:g} x {room[2]:g} mm"))


def judge(m: Measured, profile: dict, up: str = "+z") -> list[Finding]:
    """Everything the profile asks of the part."""
    out: list[Finding] = []
    axis = vec(up)
    t = flat_sheet(m, profile, out)
    walls(m, profile, out)
    holes(m, profile, out, t)
    overhangs(m, profile, axis, out)
    tools = [vec(d) if d[1] != "u" else axis * (1 if d[0] == "+" else -1) for d in profile.get("tool_directions", [])]
    if tools:
        corners(m, profile, tools, out)
        reachable(m, tools, "unreachable", "can't be reached by the tool from any of the directions the "
                                            "process works from: an undercut", out)
    draft(m, profile, axis, out)
    if profile.get("min_draft_deg") is not None:
        reachable(m, [axis, axis * -1], "undercut", "is hidden from both halves of the mould: an undercut, "
                                                    "which needs a side action", out)
    voids(m, profile, out)
    rotational(m, profile, out)
    bends(m, profile, out)
    size(m, profile, out)
    return out


def load_profiles(root: Path) -> dict[str, dict]:
    """The ruleset's profiles, with the project's own on top (design/processes.toml): changed
    limits for a process, or processes of its own."""
    profiles: dict[str, dict] = {}
    for path in (Path(__file__).resolve().parent / "processes.toml", root / "design" / "processes.toml"):
        try:
            data = tomllib.loads(path.read_text(encoding="utf-8"))
        except (OSError, tomllib.TOMLDecodeError):
            continue
        for name, values in data.items():
            if isinstance(values, dict):
                profiles[name] = {**profiles.get(name, {}), **values}
    return profiles
