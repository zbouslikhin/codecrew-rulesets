"""Deliverables: what you hand to whoever makes, buys or reviews the design.

For every part with a spec:      deliverables/<part>/drawing.svg   views and its critical dimensions
                                 deliverables/<part>/views.svg     shaded views, to judge its form
                                 deliverables/<part>/report.md     each requirement with its evidence
For every assembly with a spec:  deliverables/<name>/bom.csv       the bill of materials
                                 deliverables/<name>/report.md     parts, fits, stacks, requirements

Generated from the spec and the built geometry, never written by hand: codecrew runs this
before the checks and commits the result with the work, so a pull request shows the drawing
and the report next to the change. A deliverable is only rebuilt when what it's made from
changed. A part that doesn't build is skipped here; the validate check says why.

    python deliverables.py            write deliverables/
    python deliverables.py --force    rebuild all of them
"""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import io
import math
import re
import sys
import tomllib
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import FreeCAD as App  # noqa: E402  (must come before Part)
import Part  # noqa: E402, F401
import TechDraw  # noqa: E402

import dfm  # noqa: E402
import loads  # noqa: E402
import validate as v  # noqa: E402

OUT = "deliverables"
SHEET_W, SHEET_H = 297.0, 210.0  # A4 landscape, mm
SCALES = [(5, 1), (2, 1), (1, 1), (1, 2), (1, 5), (1, 10), (1, 20), (1, 50)]
VIEWS = {  # name: (right, up, towards the viewer)
    "Front": ((1, 0, 0), (0, 0, 1), (0, -1, 0)),
    "Top": ((1, 0, 0), (0, 1, 0), (0, 0, 1)),
    "Right": ((0, 1, 0), (0, 0, 1), (1, 0, 0)),
}


def esc(text: object) -> str:
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def load(path: Path):
    spec = importlib.util.spec_from_file_location(f"deliverable_{path.parent.name}_{path.stem}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def digest(paths: list[Path]) -> str:
    h = hashlib.sha256()
    for p in sorted(paths):
        if p.is_file():
            h.update(p.name.encode())
            h.update(p.read_bytes())
    return h.hexdigest()[:16]


def common_inputs(root: Path) -> list[Path]:
    """What every deliverable depends on: this generator, the checks it uses, the standards."""
    return [
        *HERE.glob("*.py"),
        *HERE.glob("*.toml"),
        *(root / "standards").glob("*.py"),
        root / "design" / "processes.toml",
        root / "design" / "costs.toml",
    ]


def current(folder: Path, stamp: str, files: list[str]) -> bool:
    report = folder / "report.md"
    return all((folder / f).is_file() for f in files) and report.is_file() and f"inputs: {stamp}" in report.read_text(encoding="utf-8")


# --- dimensions --------------------------------------------------------------------
def critical(design: dict, params) -> list[dict]:
    """The dimensions that matter: those an interface names, those held to a standard, those
    with a tolerance of their own, and those that prove a requirement. Each with its value,
    how it's toleranced, its limits, and what it's for."""
    uses: dict[str, list[str]] = {}

    def add(name: object, why: str) -> None:
        if isinstance(name, str) and isinstance(getattr(params, name, None), (int, float)):
            uses.setdefault(name, [])
            if why not in uses[name]:
                uses[name].append(why)

    for i in design.get("interfaces", []) if isinstance(design.get("interfaces"), list) else []:
        for name in i.get("parameters", []) if isinstance(i.get("parameters"), list) else []:
            add(name, str(i.get("id", "")))
    standards: dict[str, str] = {}
    for s in design.get("standards", []) if isinstance(design.get("standards"), list) else []:
        add(s.get("parameter"), "standard")
        if isinstance(s.get("parameter"), str):
            said = str(s.get("standard", "")).replace("_", " ")
            standards[s["parameter"]] = f"{said} {s.get('thread', '')}".strip()
    for t in design.get("tolerances", []) if isinstance(design.get("tolerances"), list) else []:
        add(t.get("parameter"), "toleranced")
    for r in design.get("requirements", []) if isinstance(design.get("requirements"), list) else []:
        for proof in r.get("proven_by", []) if isinstance(r.get("proven_by"), list) else []:
            if isinstance(proof, str) and proof.startswith("param:"):
                add(proof[6:], str(r.get("id", "")))
    rows = []
    for name, why in uses.items():
        value = float(getattr(params, name))
        found = v.tolerance_of(design, name, value) if value > 0 else None
        unit = "°" if name.endswith("_deg") else "mm"
        rows.append(
            {
                "parameter": name,
                "value": value,
                "unit": unit,
                "tolerance": found[2] if found else "none",
                "limits": f"{found[0]:.3f} to {found[1]:.3f}" if found else "",
                "standard": standards.get(name, ""),
                "for": ", ".join(w for w in why if w not in ("standard", "toleranced")),
            }
        )
    return rows


# --- the drawing -------------------------------------------------------------------
def turned(shape, right, up, toward):
    """The shape turned so that the view's right, up and towards-the-viewer are x, y and z."""
    m = App.Matrix(
        right[0], right[1], right[2], 0,
        up[0], up[1], up[2], 0,
        toward[0], toward[1], toward[2], 0,
        0, 0, 0, 1,
    )  # fmt: skip
    return shape.transformGeometry(m)


def view(shape, right, up, toward) -> tuple[str, float, float, float, float]:
    """A view as SVG paths (x right, y up), and its extent: (svg, xmin, ymin, width, height)."""
    flat = turned(shape, right, up, toward)
    box = flat.BoundBox
    raw = TechDraw.projectToSVG(flat, App.Vector(0, 0, 1), "ShowHiddenLines")
    groups = []
    for style, body in re.findall(r"<g([^>]*)>(.*?)</g>", raw, flags=re.DOTALL):
        hidden = "dasharray" in style
        body = re.sub(r'\s+id=\s*"[^"]*"', "", body).strip()
        if body:
            groups.append(("hidden" if hidden else "visible", body))
    out = "".join(f'<g class="{kind}">{body}</g>' for kind, body in sorted(groups))
    return out, box.XMin, box.YMin, box.XLength, box.YLength


def iso_axes():
    toward = App.Vector(1, -1, 1)
    toward.normalize()
    up = App.Vector(0, 0, 1) - toward * toward.z
    up.normalize()
    right = up.cross(toward)
    return tuple(right), tuple(up), tuple(toward)


def drawing(name: str, design: dict, shape, rows: list[dict], facts: list[tuple[str, str]]) -> str:
    views = {title: view(shape, *axes) for title, axes in VIEWS.items()}
    views["Isometric"] = view(shape, *iso_axes())
    fw, fh = views["Front"][3], views["Front"][4]
    tw, th = views["Top"][3], views["Top"][4]
    rw, rh = views["Right"][3], views["Right"][4]
    iw, ih = views["Isometric"][3], views["Isometric"][4]
    gap = 14.0
    area_w, area_h = 178.0, SHEET_H - 20 - 44  # left of the table, above the title block
    need_w = max(fw, tw) + max(rw, iw)
    need_h = max(fh, rh) + max(th, ih)
    scale = next(
        (a / b for a, b in SCALES if need_w * a / b + gap <= area_w and need_h * a / b + gap + 8 <= area_h),
        SCALES[-1][0] / SCALES[-1][1],
    )
    said = next(f"{a}:{b}" for a, b in SCALES if abs(a / b - scale) < 1e-9)
    left, top = 12.0, 14.0
    col2 = left + max(fw, tw) * scale + gap
    row2 = top + max(fh, rh) * scale + gap + 4
    places = {"Front": (left, top), "Right": (col2, top), "Top": (left, row2), "Isometric": (col2, row2)}
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{SHEET_W}mm" height="{SHEET_H}mm" '
        f'viewBox="0 0 {SHEET_W} {SHEET_H}" font-family="sans-serif" font-size="3">',
        f"<title>{esc(name)}: drawing</title>",
        "<style>.visible{fill:none;stroke:#000;stroke-linecap:round}.hidden{fill:none;stroke:#777;"
        "stroke-dasharray:1 0.8}.frame{fill:none;stroke:#000;stroke-width:0.35}.rule{stroke:#000;"
        "stroke-width:0.18}.cap{fill:#444;font-size:2.6px}.head{font-weight:bold}</style>",
        '<rect x="0" y="0" width="297" height="210" fill="#fff"/>',
        '<rect class="frame" x="6" y="6" width="285" height="198"/>',
    ]
    for title, (x, y) in places.items():
        svg, xmin, ymin, w, h = views[title]
        # the view's own y runs up: flip it, and move its corner to the place
        parts.append(
            f'<g transform="translate({x - xmin * scale:.3f},{y + (ymin + h) * scale:.3f}) scale({scale:.5g},{-scale:.5g})" '
            f'stroke-width="{0.35 / scale:.4g}">{svg}</g>'
        )
        parts.append(f'<text class="cap" x="{x:.2f}" y="{y + h * scale + 4:.2f}">{title}</text>')
    # hidden lines thinner than visible ones
    parts.append(f"<style>.hidden{{stroke-width:{0.18 / scale:.4g}}}</style>")

    # critical dimensions, as a table
    tx, ty, widths = 196.0, 14.0, (34.0, 14.0, 20.0, 21.0)
    heads = ("Dimension", "Nominal", "Tolerance", "Limits")
    parts.append(f'<text class="head" x="{tx}" y="{ty}">Critical dimensions (mm)</text>')
    y = ty + 5
    x = tx
    for head, w in zip(heads, widths, strict=True):
        parts.append(f'<text class="cap" x="{x}" y="{y}">{head}</text>')
        x += w
    parts.append(f'<line class="rule" x1="{tx}" y1="{y + 1.2}" x2="{tx + sum(widths)}" y2="{y + 1.2}"/>')
    for row in rows[:26]:
        y += 4.6
        cells = (
            row["parameter"].removesuffix("_mm").removesuffix("_deg"),
            f"{row['value']:g}{'°' if row['unit'] == '°' else ''}",
            row["tolerance"].replace(" (ISO 273)", ""),
            row["limits"],
        )
        x = tx
        for cell, w in zip(cells, widths, strict=True):
            parts.append(f'<text x="{x}" y="{y}" font-size="2.6">{esc(cell)}</text>')
            x += w
    if len(rows) > 26:
        parts.append(f'<text class="cap" x="{tx}" y="{y + 5}">and {len(rows) - 26} more: see report.md</text>')
    if not rows:
        parts.append(f'<text class="cap" x="{tx}" y="{y + 5}">none declared in the spec</text>')

    # title block
    by = SHEET_H - 6 - 34
    parts.append(f'<rect class="frame" x="6" y="{by}" width="285" height="34"/>')
    parts.append(f'<text class="head" x="10" y="{by + 7}" font-size="5">{esc(name)}</text>')
    purpose = str(design.get("purpose", ""))
    parts.append(f'<text x="10" y="{by + 12.5}" font-size="2.8">{esc(purpose[:150])}</text>')
    facts = [*facts, ("Scale", said), ("Projection", "views are labelled")]
    for n, (label, value) in enumerate(facts):
        fx = 10 + (n % 4) * 70
        fy = by + 19 + (n // 4) * 7
        parts.append(f'<text class="cap" x="{fx}" y="{fy}">{esc(label)}</text>')
        parts.append(f'<text x="{fx}" y="{fy + 3.4}" font-size="2.9">{esc(value)[:44]}</text>')
    parts.append(
        f'<text class="cap" x="291" y="{SHEET_H - 2.2}" text-anchor="end" font-size="2.2">Generated by codecrew from '
        f"design/{esc(name)}.spec.toml and parts/{esc(name)}.py. Not edited by hand.</text>"
    )
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


# --- shaded views, for looking at -----------------------------------------------------
LIGHT = (-0.35, -0.5, 0.79)
MAX_TRIANGLES = 2500


def shaded(shape, toward, up) -> tuple[str, float, float]:
    """The part as flat-shaded triangles seen from `toward`: (svg polygons, width, height).
    Painted back to front; enough to judge proportion and form, not a rendering."""
    t = App.Vector(*toward)
    t.normalize()
    u = App.Vector(*up) - t * App.Vector(*up).dot(t)
    u.normalize()
    r = u.cross(t)
    light = App.Vector(*LIGHT)
    light.normalize()
    import MeshPart

    # coarse enough to keep the file small: the angle between neighbouring facets is what
    # decides how many there are on round surfaces
    linear = max(shape.BoundBox.DiagonalLength / 200, 0.05)
    for angular in (0.35, 0.6, 1.0):
        mesh = MeshPart.meshFromShape(Shape=shape.copy(), LinearDeflection=linear, AngularDeflection=angular)
        if mesh.CountFacets <= MAX_TRIANGLES:
            break
    points, triangles = mesh.Topology
    flat = [(p.dot(r), p.dot(u), p.dot(t)) for p in points]
    xs, ys = [f[0] for f in flat], [f[1] for f in flat]
    x0, y1 = min(xs), max(ys)
    drawn = []
    for a, b, c in triangles:
        normal = (points[b] - points[a]).cross(points[c] - points[a])
        if normal.Length < 1e-12:
            continue
        normal.normalize()
        if normal.dot(t) <= 0:
            continue  # facing away
        shade = int(105 + 135 * max(0.0, normal.dot(light)))
        depth = (flat[a][2] + flat[b][2] + flat[c][2]) / 3
        corners = " ".join(f"{flat[i][0] - x0:.2f},{y1 - flat[i][1]:.2f}" for i in (a, b, c))
        colour = f"rgb({shade},{shade},{shade + 6})"
        drawn.append((depth, f'<polygon points="{corners}" fill="{colour}" stroke="{colour}"/>'))
    drawn.sort(key=lambda d: d[0])
    return "".join(svg for _, svg in drawn), max(xs) - x0, y1 - min(ys)


def views(name: str, shape) -> str:
    """Two shaded views from fixed corners, side by side: the same angles for every part, so
    parts can be compared."""
    angles = [("From the front right, above", (1, -1, 0.8)), ("From the back left, above", (-1, 1, 0.8))]
    made = [(title, *shaded(shape, toward, (0, 0, 1))) for title, toward in angles]
    # each view gets a column wide enough for its caption, whatever the part's shape
    font = max(max(m[2] for m in made) / 16, max(m[3] for m in made) / 40)
    column = max(max(m[2] for m in made), font * 16)
    tall = max(m[3] for m in made)
    gap, pad, cap = font * 2, font * 1.5, font * 2.2
    width = column * len(made) + gap * (len(made) - 1) + 2 * pad
    height = tall + 2 * pad + cap
    shown = min(900.0, max(480.0, width * 6))
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.2f} {height:.2f}" '
        f'width="{shown:.0f}" height="{shown * height / width:.0f}" font-family="sans-serif">',
        f"<title>{esc(name)}: shaded views</title>",
        f'<rect width="{width:.2f}" height="{height:.2f}" fill="#fff"/>',
    ]
    x = pad
    for title, svg, w, h in made:
        out.append(
            f'<g transform="translate({x + (column - w) / 2:.2f},{pad + tall - h:.2f})" '
            f'stroke-width="{font * 0.02:.3f}" stroke-linejoin="round">{svg}</g>'
        )
        out.append(
            f'<text x="{x + column / 2:.2f}" y="{height - pad * 0.6:.2f}" font-size="{font:.2f}" '
            f'text-anchor="middle" fill="#444">{title}</text>'
        )
        x += column + gap
    out.append("</svg>")
    return "\n".join(out) + "\n"


# --- cost --------------------------------------------------------------------------
def cost(root: Path, design: dict, shape, mass_g: float | None) -> list[str]:
    """A cost estimate from the project's own rates (design/costs.toml). Without rates for the
    part's material and process there is no estimate: prices aren't guessed."""
    try:
        rates = tomllib.loads((root / "design" / "costs.toml").read_text(encoding="utf-8"))
    except OSError:
        return ["No cost estimate: the project has no `design/costs.toml` with its rates."]
    except tomllib.TOMLDecodeError as e:
        return [f"No cost estimate: `design/costs.toml` isn't valid TOML ({e})."]
    currency = str(rates.get("currency", ""))
    material = str(design.get("material", ""))
    per_kg = (rates.get("materials") or {}).get(material) if isinstance(rates.get("materials"), dict) else None
    quantity = design.get("quantity", 1) if isinstance(design.get("quantity"), int) else 1
    lines: list[str] = []
    box = v.extent(shape)
    block_cm3 = box.XLength * box.YLength * box.ZLength / 1000
    part_cm3 = shape.Volume / 1000
    density = mass_g / part_cm3 if mass_g and part_cm3 else None
    for process in design.get("processes", []) if isinstance(design.get("processes"), list) else []:
        p = (rates.get("processes") or {}).get(process) if isinstance(rates.get("processes"), dict) else None
        if not isinstance(p, dict) or not isinstance(per_kg, (int, float)) or density is None:
            lacking = f"material {material}" if not isinstance(per_kg, (int, float)) else f"process {process}"
            lines.append(f"- **{process}**: no estimate, `design/costs.toml` has no rate for {lacking}.")
            continue
        from_block = p.get("stock") == "block"
        bought_cm3 = block_cm3 if from_block else part_cm3 * (1 + float(p.get("waste", 0.0)))
        worked_cm3 = (block_cm3 - part_cm3) if from_block else part_cm3
        material_cost = bought_cm3 * density / 1000 * float(per_kg)
        rate = float(p.get("rate_per_hour", 0.0))
        speed = float(p.get("cm3_per_hour", 0.0))
        hours = worked_cm3 / speed if speed > 0 else 0.0
        setup = float(p.get("setup_minutes", 0.0)) / 60 * rate / quantity
        tooling = float(p.get("tooling", 0.0)) / quantity
        total = material_cost + hours * rate + setup + tooling
        what = "removed from a block" if from_block else "built up"
        lines += [
            f"- **{process}**: about **{total:.2f} {currency}** each, at {quantity} made.",
            f"  - material: {bought_cm3:.1f} cm³ of {material} at {per_kg:g} {currency}/kg = {material_cost:.2f}",
            f"  - machine: {worked_cm3:.1f} cm³ {what} at {speed:g} cm³/h = {hours * 60:.0f} min at {rate:g} {currency}/h = {hours * rate:.2f}",
            f"  - setup: {p.get('setup_minutes', 0):g} min shared by {quantity} = {setup:.2f}; tooling: {p.get('tooling', 0):g} shared by {quantity} = {tooling:.2f}",
        ]
    if lines:
        lines.append("")
        lines.append("A rough figure from volumes and the rates in `design/costs.toml`: for comparing designs and processes, not a quotation.")
    return lines


# --- a part ------------------------------------------------------------------------
def part(root: Path, path: Path, force: bool) -> str | None:
    name = path.stem
    spec_path = root / "design" / f"{name}.spec.toml"
    design = v.load_spec(root, name)
    if design.get("kind") != "part":
        return None
    folder = root / OUT / name
    stamp = digest([path, spec_path, *common_inputs(root)])
    if not force and current(folder, stamp, ["drawing.svg", "views.svg"]):
        return None
    module = load(path)
    params = module.PARAMS
    shape = module.build(params)
    if v.check_shape(shape, "result") is not None:
        return None
    box = v.extent(shape)
    material = v.materials.get(str(design.get("material"))) if v.materials is not None else None
    density = getattr(module, "DENSITY_G_CM3", None) or (material.density_g_cm3 if material else None)
    mass = shape.Volume / 1000 * density if isinstance(density, (int, float)) else None
    rows = critical(design, params)
    processes = [p for p in design.get("processes", []) if isinstance(p, str)] if isinstance(design.get("processes"), list) else []
    profiles = dfm.load_profiles(root)
    facts = [
        ("Material", str(design.get("material", ""))),
        ("Process", ", ".join(str(profiles.get(p, {}).get("title", p)) for p in processes)),
        ("General tolerance", f"ISO 2768-{design['general_tolerance']}" if design.get("general_tolerance") else "none"),
        ("Mass", f"{mass:.1f} g" if mass is not None else "unknown"),
        ("Envelope", f"{box.XLength:.1f} x {box.YLength:.1f} x {box.ZLength:.1f} mm"),
        ("Quantity", str(design.get("quantity", ""))),
    ]
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "drawing.svg").write_text(drawing(name, design, shape, rows, facts), encoding="utf-8")
    (folder / "views.svg").write_text(views(name, shape), encoding="utf-8")

    out = [f"# {name}: design report", "", f"_{design.get('purpose', '')}_", ""]
    out += ["![shaded views](views.svg)", "", "![drawing](drawing.svg)", "", "## What it is", ""]
    out += [f"- **{label}:** {value}" for label, value in facts]
    look = design.get("appearance")
    if isinstance(look, dict):
        seen = "seen" if look.get("visible") else "not seen"
        held = "touched" if look.get("touched") else "not touched"
        cmf = ", ".join(str(look[k]) for k in ("colour", "finish") if look.get(k))
        out.append(f"- **Appearance:** {seen}, {held}" + (f"; {cmf}" if cmf else ""))
    out += ["", "## Requirements and their evidence", "", "| ID | Requirement | Evidence |", "|---|---|---|"]
    envelope, target = design.get("envelope_mm"), design.get("mass_g")
    carried = []
    if v.materials is not None and design.get("loads"):
        try:
            from standards import strength

            carried = loads.evaluate(design, params, profiles, strength, v.materials)
        except ImportError:
            pass
    by_name = {r["parameter"]: r for r in rows}
    for r in design.get("requirements", []) if isinstance(design.get("requirements"), list) else []:
        evidence = []
        for proof in r.get("proven_by", []) if isinstance(r.get("proven_by"), list) else []:
            kind, _, what = str(proof).partition(":")
            if kind == "test":
                evidence.append(f"test `tests/test_{name}.py::{what}`")
            elif kind == "param" and what in by_name:
                row = by_name[what]
                limits = f", {row['tolerance']}: {row['limits']}" if row["limits"] else ""
                evidence.append(f"`{what}` = {row['value']:g} {row['unit']}{limits}")
            elif proof == "check:envelope" and isinstance(envelope, dict):
                evidence.append(
                    f"measured {box.XLength:.1f} x {box.YLength:.1f} x {box.ZLength:.1f} mm, within "
                    f"{envelope.get('x', 0):g} x {envelope.get('y', 0):g} x {envelope.get('z', 0):g} mm"
                )
            elif proof == "check:strength" and carried:
                evidence.append("; ".join(
                    f"{c.ident}: safety factor {loads._factor(c.factor) if c.factor is not None else '?'}"
                    f" (needs {c.target:g})" + ("" if c.ok else " **not met**") for c in carried))
            elif proof == "check:mass" and isinstance(target, dict) and mass is not None:
                evidence.append(f"{mass:.1f} g, at most {target.get('max', 0):g} g")
            else:
                evidence.append(str(proof))
        out.append(f"| {r.get('id', '')} | {str(r.get('text', '')).replace('|', '/')} | {'; '.join(evidence)} |")
    if design.get("interfaces"):
        out += ["", "## Interfaces", "", "| ID | Mates with | Dimensions | Fit |", "|---|---|---|---|"]
        for i in design["interfaces"]:
            dims = ", ".join(f"`{n}`" for n in i.get("parameters", []))
            out.append(f"| {i.get('id', '')} | {i.get('mates_with', '')} | {dims} | {i.get('fit', '')} |")
    out += ["", "## Critical dimensions", ""]
    if rows:
        out += ["| Dimension | Nominal | Tolerance | Limits | Standard | For |", "|---|---|---|---|---|---|"]
        out += [
            f"| `{r['parameter']}` | {r['value']:g} {r['unit']} | {r['tolerance']} | {r['limits']} | {r['standard']} | {r['for']} |"
            for r in rows
        ]
    else:
        out.append("None declared in the spec.")
    out += ["", "## Manufacturability", ""]
    measured = dfm.measure(shape) if processes else None
    orientation = design.get("orientation")
    up = orientation.get("up", "+z") if isinstance(orientation, dict) and orientation.get("up") in dfm.AXES else "+z"
    for process in processes:
        profile = profiles.get(process)
        if not isinstance(profile, dict) or measured is None:
            out.append(f"- **{process}**: no profile.")
            continue
        found = dfm.judge(measured, profile, up)
        title = profile.get("title", process)
        out.append(f"- **{title}**: " + ("no findings." if not found else f"{len(found)} finding(s):"))
        out += [f"  - {f.message}" for f in found]
    if carried:
        out += ["", "## Strength", "", "| Load | What | Calculation | Result |", "|---|---|---|---|"]
        for c in carried:
            verdict = "carried" if c.ok else "**" + ", ".join(code for code, _ in c.findings) + "**"
            out.append(f"| {c.ident} | {c.text.replace('|', '/')} | {c.model.replace('_', ' ')}: {c.said} | {verdict} |")
        out += [
            "",
            "Hand calculations for a straight member of constant section under a static load "
            "(`standards/strength.py`): a first check, not an analysis. Fatigue, creep, impact, "
            "buckling and the stress around details are not covered.",
        ]
    out += ["", "## Cost", "", *cost(root, design, shape, mass), ""]
    out += [f"<!-- generated by codecrew; inputs: {stamp} -->", ""]
    (folder / "report.md").write_text("\n".join(out), encoding="utf-8")
    return name


# --- an assembly -------------------------------------------------------------------
def assembly(root: Path, spec_path: Path, force: bool) -> str | None:
    name = spec_path.name.removesuffix(".spec.toml")
    design = v.load_spec(root, name)
    if design.get("kind") != "assembly" or design.get("status") == "proposed":
        return None  # a proposed assembly has nothing to list yet
    members = [m for m in design.get("parts", []) if isinstance(m, dict)]
    own = [str(m["part"]) for m in members if isinstance(m.get("part"), str)]
    inputs = [spec_path, root / "assemblies" / f"{name}.py", *common_inputs(root)]
    for p in own:
        inputs += [root / "parts" / f"{p}.py", root / "design" / f"{p}.spec.toml"]
    folder = root / OUT / name
    stamp = digest(inputs)
    if not force and current(folder, stamp, ["bom.csv"]):
        return None
    cache: dict = {}
    rows = []
    for n, m in enumerate(members, 1):
        quantity = m.get("quantity", 1) if isinstance(m.get("quantity", 1), int) else 1
        if isinstance(m.get("part"), str):
            pname = m["part"]
            pdesign = v.load_spec(root, pname)
            mass = None
            try:
                module = load(root / "parts" / f"{pname}.py")
                shape = module.build(module.PARAMS)
                material = v.materials.get(str(pdesign.get("material"))) if v.materials is not None else None
                density = getattr(module, "DENSITY_G_CM3", None) or (material.density_g_cm3 if material else None)
                mass = shape.Volume / 1000 * density if isinstance(density, (int, float)) else None
            except Exception:  # noqa: BLE001  (the part's own check reports it)
                pass
            processes = ", ".join(str(p) for p in pdesign.get("processes", [])) if isinstance(pdesign.get("processes"), list) else ""
            rows.append([n, "part", pname, quantity, pdesign.get("material", ""), processes, mass])
        elif isinstance(m.get("standard"), str):
            rows.append([n, "standard part", m["standard"], quantity, "", "bought", None])
        elif isinstance(m.get("reference"), str):
            rows.append([n, "reference", m["reference"], quantity, "", "not supplied: what it must fit", None])
    folder.mkdir(parents=True, exist_ok=True)
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(["item", "kind", "name", "quantity", "material", "made by", "mass each (g)", "mass total (g)"])
    for r in rows:
        each = f"{r[6]:.1f}" if r[6] is not None else ""
        total = f"{r[6] * r[3]:.1f}" if r[6] is not None else ""
        writer.writerow([*r[:6], each, total])
    (folder / "bom.csv").write_text(buffer.getvalue(), encoding="utf-8")

    known = [r[6] * r[3] for r in rows if r[6] is not None]
    out = [f"# {name}: assembly report", "", f"_{design.get('purpose', '')}_", "", "## Bill of materials", ""]
    out += ["| Item | Kind | Name | Quantity | Material | Made by | Mass each | Mass total |", "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        each = f"{r[6]:.1f} g" if r[6] is not None else ""
        total = f"{r[6] * r[3]:.1f} g" if r[6] is not None else ""
        link = f"[{r[2]}](../{r[2]}/report.md)" if r[1] == "part" else str(r[2])
        out.append(f"| {r[0]} | {r[1]} | {link} | {r[3]} | {r[4]} | {r[5]} | {each} | {total} |")
    out += ["", f"Mass of the parts made here: {sum(known):.1f} g. Standard and reference parts aren't weighed.", ""]
    joints = [j for j in design.get("joints", []) if isinstance(j, dict)]
    if joints:
        out += ["## Joints", "", "| Joint | Between | Kind | Fit, worst case |", "|---|---|---|---|"]
        for n, j in enumerate(joints, 1):
            fit = j.get("fit")
            said = ""
            if isinstance(fit, dict) and v.tolerances is not None:
                hole = v.part_dimension(root, str(fit.get("hole", "")), cache)
                shaft = v.part_dimension(root, str(fit.get("shaft", "")), cache)
                if hole and shaft:
                    least, most, kind = v.tolerances.fit(hole[:2], shaft[:2])
                    said = f"{hole[3]:g} {hole[2]} / {shaft[2]}: a {kind} fit, clearance {least:+.3f} to {most:+.3f} mm"
            out.append(f"| {n} | {j.get('a', '')} and {j.get('b', '')} | {j.get('kind', 'fixed')} | {said} |")
        out.append("")
    stacks = [s for s in design.get("stacks", []) if isinstance(s, dict)]
    if stacks:
        out += ["## Stacks of dimensions, worst case", "", "| ID | What | Chain | Result | Must be |", "|---|---|---|---|---|"]
        for s in stacks:
            least = most = nominal = 0.0
            ok = True
            for term in s.get("terms", []) if isinstance(s.get("terms"), list) else []:
                found = v.part_dimension(root, str(term), cache)
                if found is None:
                    ok = False
                    break
                sign = 1 if str(term)[0] == "+" else -1
                nominal += sign * found[3]
                least += found[0] if sign > 0 else -found[1]
                most += found[1] if sign > 0 else -found[0]
            result = f"{nominal:.3f} mm ({least:.3f} to {most:.3f})" if ok else "not toleranced throughout"
            limits = " to ".join(f"{s[k]:g}" for k in ("min_mm", "max_mm") if isinstance(s.get(k), (int, float)))
            out.append(f"| {s.get('id', '')} | {s.get('text', '')} | {' '.join(map(str, s.get('terms', [])))} | {result} | {limits} mm |")
        out.append("")
    out += ["## Requirements and their evidence", "", "| ID | Requirement | Evidence |", "|---|---|---|"]
    for r in design.get("requirements", []) if isinstance(design.get("requirements"), list) else []:
        evidence = []
        for proof in r.get("proven_by", []) if isinstance(r.get("proven_by"), list) else []:
            kind, _, what = str(proof).partition(":")
            if kind == "test":
                evidence.append(f"test `tests/test_{name}.py::{what}`")
            elif kind == "part":
                p, _, req = what.partition(":")
                evidence.append(f"requirement {req} of [{p}](../{p}/report.md)")
            else:
                evidence.append(str(proof))
        out.append(f"| {r.get('id', '')} | {str(r.get('text', '')).replace('|', '/')} | {'; '.join(evidence)} |")
    out += ["", f"<!-- generated by codecrew; inputs: {stamp} -->", ""]
    (folder / "report.md").write_text("\n".join(out), encoding="utf-8")
    return name


def main() -> int:
    root = Path.cwd()
    sys.path.insert(0, str(root))
    force = "--force" in sys.argv
    made = []
    for path in sorted((root / "parts").glob("*.py")) if (root / "parts").is_dir() else []:
        if path.name == "__init__.py":
            continue
        try:
            done = part(root, path, force)
        except Exception as e:  # noqa: BLE001  (a part that doesn't build: validate says why)
            print(f"skipped {path.stem}: {type(e).__name__}: {e}", file=sys.stderr)
            continue
        if done:
            made.append(done)
    for spec_path in sorted((root / "design").glob("*.spec.toml")) if (root / "design").is_dir() else []:
        try:
            done = assembly(root, spec_path, force)
        except Exception as e:  # noqa: BLE001
            print(f"skipped {spec_path.name}: {type(e).__name__}: {e}", file=sys.stderr)
            continue
        if done:
            made.append(done)
    if made:
        print(f"deliverables written for: {', '.join(made)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
