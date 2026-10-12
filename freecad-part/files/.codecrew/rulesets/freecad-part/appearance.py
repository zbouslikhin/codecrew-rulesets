"""Industrial design, as far as it can be measured: what a hand and an eye meet.

For a part its spec says is touched: no sharp outer edges. For one that is visible: its radii
come from one small family. For what a hand holds: sizes within what hands need
(ergonomics.toml, and the project's own design/ergonomics.toml).

Proportion, visual weight and whether it looks like it belongs with its neighbours can't be
measured: for those the deliverables include shaded views, and the reviewer has a checklist.
"""

from __future__ import annotations

import math
import tomllib
from pathlib import Path

import FreeCAD as App  # must come before Part
import Part

import dfm

SHARP_DEG = 60.0  # an outer edge whose faces turn by this much or more is sharp to the hand
MAX_RADII = 3  # a visible part uses at most this many different radii


def load_ergonomics(root: Path) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for path in (Path(__file__).resolve().parent / "ergonomics.toml", root / "design" / "ergonomics.toml"):
        try:
            data = tomllib.loads(path.read_text(encoding="utf-8"))
        except (OSError, tomllib.TOMLDecodeError):
            continue
        for name, values in data.items():
            if isinstance(values, dict):
                out[name] = {**out.get(name, {}), **values}
    return out


def sharp_outer_edges(shape: Part.Shape, rests_on: App.Vector | None) -> list[tuple[App.Vector, float, float]]:
    """Outer edges with no break: (a point on it, its length, the angle its faces turn by).
    Edges of the face the part rests on are left out: they lie against what it sits on."""
    floor = None
    if rests_on is not None:
        floor = max(v.Point.dot(rests_on) for v in shape.Vertexes)
    found = []
    for edge in shape.Edges:
        faces = shape.ancestorsOfType(edge, Part.Face)
        if len(faces) != 2 or edge.Length < 1e-6:
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
            if dfm.inside(shape, mid + n * dfm.STEP):
                n = n * -1
            normals.append(n)
        if len(normals) != 2:
            continue
        turn = math.degrees(math.acos(max(-1.0, min(1.0, normals[0].dot(normals[1])))))
        if turn < SHARP_DEG - 1e-6:
            continue  # tangent, or broken by a chamfer
        tangent = edge.tangentAt(param)
        away = normals[0].cross(tangent)
        if away.Length < dfm.EPS:
            continue
        away.normalize()
        if not faces[0].isInside(mid + away * (dfm.STEP * 5), 1e-3, True):
            away = away * -1
        if away.dot(normals[1]) > -0.02:
            continue  # an internal corner: a finger doesn't meet it
        if floor is not None and all(abs(v.Point.dot(rests_on) - floor) < 1e-4 for v in edge.Vertexes):
            continue
        found.append((mid, edge.Length, turn))
    return found


def radii(shape: Part.Shape) -> list[float]:
    """The different radii of the part's rounded edges (fillets, inside and out), not of its
    holes or of the round body of a turned part."""
    seen: set[float] = set()
    for face in shape.Faces:
        surface = face.Surface
        if isinstance(surface, Part.Toroid):
            seen.add(round(surface.MinorRadius, 3))
        elif isinstance(surface, Part.Cylinder):
            u0, u1, _, _ = face.ParameterRange
            if u1 - u0 < math.pi + 1e-3:  # a part of a turn: a rounded edge, not a hole or a shaft
                seen.add(round(surface.Radius, 3))
        elif isinstance(surface, Part.Sphere):
            seen.add(round(surface.Radius, 3))
    return sorted(seen)


def judge(root: Path, shape: Part.Shape, design: dict, params) -> list[dfm.Finding]:
    look = design.get("appearance")
    if not isinstance(look, dict):
        return []
    out: list[dfm.Finding] = []
    if look.get("touched") is True:
        rests = look.get("rests_on")
        down = dfm.vec(rests) if rests in dfm.AXES else None
        sharp = sharp_outer_edges(shape, down)
        if sharp:
            total = sum(length for _, length, _ in sharp)
            worst = max(sharp, key=lambda s: s[1])
            out.append(dfm.Finding(
                "sharp-edge",
                f"{len(sharp)} outer edge(s) are sharp, {total:.0f} mm in all, the longest at {dfm.where(worst[0])}: "
                "a hand touches this part. Break them with a radius or a chamfer"
                + ("" if down is not None else " (edges of the face it rests on are exempt once the spec says rests_on)"),
            ))
    if look.get("visible") is True:
        used = radii(shape)
        most = look.get("max_radii", MAX_RADII)
        if isinstance(most, int) and len(used) > most:
            out.append(dfm.Finding(
                "radius-family",
                f"the part uses {len(used)} different radii ({', '.join(f'{r:g}' for r in used)} mm): a visible part "
                f"keeps to {most} or fewer, so its edges read as one family",
            ))
    ranges = load_ergonomics(root)
    for grip in design.get("grips", []) if isinstance(design.get("grips"), list) else []:
        kind, name = grip.get("kind"), grip.get("parameter")
        value = getattr(params, str(name), None)
        limits = ranges.get(str(kind))
        if not isinstance(limits, dict) or not isinstance(value, (int, float)):
            continue  # the spec check says what's wrong with the entry
        low, high = limits.get("min"), limits.get("max")
        if (isinstance(low, (int, float)) and value < low - 1e-9) or (isinstance(high, (int, float)) and value > high + 1e-9):
            span = " to ".join(f"{x:g}" for x in (low, high) if isinstance(x, (int, float)))
            bound = f"{span} mm" if low is not None and high is not None else f"at least {low:g} mm" if low is not None else f"at most {high:g} mm"
            out.append(dfm.Finding(
                "grip-size",
                f"{name} is {value:g} mm; {limits.get('title', kind)} is {bound}",
            ))
    return out
