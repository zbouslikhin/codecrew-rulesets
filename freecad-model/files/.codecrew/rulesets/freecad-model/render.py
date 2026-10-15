"""Pictures of a part, an assembly or a reference file, for the agent and for you.

    python -B .codecrew/rulesets/freecad-model/render.py parts/tray_tile.py
    python -B .codecrew/rulesets/freecad-model/render.py assemblies/drawer.py --views iso,front

Writes exports/renders/<name>/<view>.png (3D, front, top, side), a summary of what's in them
(exports/renders/<name>/summary.json) and the meshes for the dashboard's 3D preview
(exports/preview/<name>/). Prints the summary.

What the pictures show:
- every part in its own colour, the same colour for every copy of a part; reference geometry
  (reference/*.step) in grey; standard parts (screws) in blue
- the outline of every edge that can be seen
- in red, on top of everything: where two components occupy the same space
- with --xray (the default for assemblies): standard parts shown through what hides them
Coordinates: x to the right, y away from you (to the back), z up. "front" looks at the model
from the front (along +y), "top" from above, "side" from the right (along -x).
"""

from __future__ import annotations

import argparse
import json
import math
import struct
import sys
from pathlib import Path

import FreeCAD  # noqa: F401  must come before Part
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from model import Component, LoadError, load, overlaps  # noqa: E402

W, H = 960, 720
BACKGROUND = (245, 245, 244)
EDGE = (32, 32, 32)
OVERLAP = (229, 72, 77)
STANDARD = (59, 130, 246)
REFERENCE = (160, 164, 170)
PALETTE = [(214, 190, 140), (143, 179, 154), (179, 154, 201), (201, 154, 143), (143, 169, 201), (201, 192, 143)]

# camera: where it is, as a direction from the model, and which way is up on the picture
VIEWS = {
    "iso": ((1.0, -1.0, 0.8), (0.0, 0.0, 1.0)),
    "front": ((0.0, -1.0, 0.0), (0.0, 0.0, 1.0)),
    "top": ((0.0, 0.0, 1.0), (0.0, 1.0, 0.0)),
    "side": ((1.0, 0.0, 0.0), (0.0, 0.0, 1.0)),
}
NAMES = {"iso": "3D", "front": "front", "top": "top", "side": "side (from the right)"}


def colour_of(c: Component, order: dict[str, int]) -> tuple[int, int, int]:
    if c.kind == "standard":
        return STANDARD
    if c.kind == "reference":
        return REFERENCE
    base = c.name.split(":")[0]
    return PALETTE[order.setdefault(base, len(order)) % len(PALETTE)]


def mesh(shape, tolerance: float) -> np.ndarray:
    """The shape's surface as triangles: an (n, 3, 3) array of corner points."""
    points, triangles = shape.tessellate(tolerance)
    if not triangles:
        return np.zeros((0, 3, 3))
    pts = np.array([(p.x, p.y, p.z) for p in points], dtype=float)
    return pts[np.array(triangles, dtype=int)]


def edges_of(shape, tolerance: float) -> list[np.ndarray]:
    out = []
    for edge in shape.Edges:
        try:
            pts = edge.discretize(Deflection=tolerance)
        except Exception:  # noqa: BLE001
            continue
        if len(pts) >= 2:
            out.append(np.array([(p.x, p.y, p.z) for p in pts], dtype=float))
    return out


class Camera:
    def __init__(self, view: str, lo: np.ndarray, hi: np.ndarray) -> None:
        eye, up = VIEWS[view]
        self.forward = -np.array(eye) / np.linalg.norm(eye)
        right = np.cross(self.forward, up)
        self.right = right / np.linalg.norm(right)
        self.up = np.cross(self.right, self.forward)
        corners = np.array([[x, y, z] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])])
        sx, sy = corners @ self.right, -(corners @ self.up)
        span = max(sx.max() - sx.min(), 1e-6), max(sy.max() - sy.min(), 1e-6)
        self.scale = min((W * 0.86) / span[0], (H * 0.78) / span[1])  # pixels per mm
        self.ox = W / 2 - self.scale * (sx.max() + sx.min()) / 2
        self.oy = H / 2 + 14 - self.scale * (sy.max() + sy.min()) / 2

    def project(self, pts: np.ndarray) -> np.ndarray:
        """mm -> (pixel x, pixel y, depth in mm), for (..., 3) points."""
        x = pts @ self.right * self.scale + self.ox
        y = -(pts @ self.up) * self.scale + self.oy
        return np.stack([x, y, pts @ self.forward], axis=-1)


def rasterise(tris: np.ndarray, colours: np.ndarray, cam: Camera, zbuf: np.ndarray, img: np.ndarray,
              depth_test: bool = True, alpha: float = 1.0) -> None:
    """Fills the triangles into img, nearest first wins (z-buffer), flat-shaded."""
    if len(tris) == 0:
        return
    normals = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
    lengths = np.linalg.norm(normals, axis=1)
    keep = lengths > 1e-12
    tris, colours, normals = tris[keep], colours[keep], normals[keep] / lengths[keep][:, None]
    light = -cam.forward * 0.75 + cam.up * 0.55 + cam.right * 0.35
    light /= np.linalg.norm(light)
    shade = 0.42 + 0.58 * np.abs(normals @ light)
    shaded = np.clip(colours * shade[:, None], 0, 255)
    screen = cam.project(tris)
    for (a, b, c), col in zip(screen, shaded, strict=True):
        x0, x1 = int(max(min(a[0], b[0], c[0]), 0)), int(min(max(a[0], b[0], c[0]) + 1, W))
        y0, y1 = int(max(min(a[1], b[1], c[1]), 0)), int(min(max(a[1], b[1], c[1]) + 1, H))
        if x0 >= x1 or y0 >= y1:
            continue
        area = (b[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (b[1] - a[1])
        if abs(area) < 1e-9:
            continue
        xs = (np.arange(x0, x1) + 0.5)[None, :]
        ys = (np.arange(y0, y1) + 0.5)[:, None]
        w0 = ((b[0] - xs) * (c[1] - ys) - (c[0] - xs) * (b[1] - ys)) / area
        w1 = ((c[0] - xs) * (a[1] - ys) - (a[0] - xs) * (c[1] - ys)) / area
        w2 = 1.0 - w0 - w1
        inside = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
        inside = np.broadcast_to(inside, (y1 - y0, x1 - x0))
        if not inside.any():
            continue
        depth = np.broadcast_to(w0 * a[2] + w1 * b[2] + w2 * c[2], inside.shape)
        region = zbuf[y0:y1, x0:x1]
        win = inside & (depth < region) if depth_test else inside
        if depth_test:
            region[win] = depth[win]
        target = img[y0:y1, x0:x1]
        target[win] = target[win] * (1 - alpha) + col * alpha


def draw_edges(draw: ImageDraw.ImageDraw, polylines: list[np.ndarray], cam: Camera, zbuf: np.ndarray,
               eps: float, colour=EDGE, width: int = 1) -> None:
    for line in polylines:
        s = cam.project(line)
        for p, q in zip(s[:-1], s[1:], strict=True):
            n = max(int(math.hypot(q[0] - p[0], q[1] - p[1])), 1)
            t = np.linspace(0.0, 1.0, n + 1)
            pts = p[None, :] * (1 - t)[:, None] + q[None, :] * t[:, None]
            xi = np.clip(pts[:, 0].astype(int), 0, W - 1)
            yi = np.clip(pts[:, 1].astype(int), 0, H - 1)
            near = zbuf[yi, xi]
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):  # an edge sits between two faces
                near = np.maximum(near, zbuf[np.clip(yi + dy, 0, H - 1), np.clip(xi + dx, 0, W - 1)])
            seen = pts[:, 2] <= near + eps
            run: list[tuple[float, float]] = []
            for k in range(len(pts)):
                if seen[k]:
                    run.append((float(pts[k, 0]), float(pts[k, 1])))
                elif run:
                    if len(run) > 1:
                        draw.line(run, fill=colour, width=width)
                    run = []
            if len(run) > 1:
                draw.line(run, fill=colour, width=width)


def nice_length(mm: float) -> float:
    k = 10 ** math.floor(math.log10(mm))
    for m in (5, 2, 1):
        if m * k <= mm:
            return m * k
    return k


def font(size: int):
    for name in ("DejaVuSans.ttf", "Arial.ttf", "LiberationSans-Regular.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def label(draw: ImageDraw.ImageDraw, xy: tuple[float, float], text: str, fill, size: int = 13) -> None:
    f = font(size)
    x, y = xy
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            draw.text((x + dx, y + dy), text, font=f, fill=BACKGROUND)
    draw.text((x, y), text, font=f, fill=fill)


def write_stl(path: Path, tris: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    n = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0]) if len(tris) else np.zeros((0, 3))
    length = np.linalg.norm(n, axis=1)
    n[length > 0] /= length[length > 0][:, None]
    rows = np.zeros(len(tris), dtype=[("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
    rows["n"], rows["v"] = n, tris
    with path.open("wb") as fh:
        fh.write(b"codecrew preview".ljust(80, b" "))
        fh.write(struct.pack("<I", len(tris)))
        fh.write(rows.tobytes())


class Scene:
    """Everything a picture is drawn from: each component's triangles, colour and edges, and
    the solids where components overlap."""

    def __init__(self, components: list[Component], tol: float, order: dict[str, int], assembly: bool) -> None:
        self.components = components
        self.meshes = [(c, mesh(c.shape, tol), np.array(colour_of(c, order), dtype=float)) for c in components]
        self.lines = {c.name: edges_of(c.shape, tol) for c in components}
        self.shared = overlaps(components) if assembly else []
        self.shared_meshes = [(a, b, s, mesh(s, max(0.02, tol / 2))) for a, b, s in self.shared]
        self.diag = max(
            (c.shape.BoundBox.DiagonalLength for c in components), default=1.0
        )


def draw_scene(scene: Scene, view: str, lo, hi, title: str, xray: bool, labels: bool) -> Image.Image:
    cam = Camera(view, lo, hi)
    img = np.empty((H, W, 3), dtype=float)
    img[:] = BACKGROUND
    zbuf = np.full((H, W), np.inf)
    for _c, tris, col in scene.meshes:
        rasterise(tris, np.repeat(col[None, :], len(tris), axis=0), cam, zbuf, img)
    picture = Image.fromarray(img.astype(np.uint8))
    draw = ImageDraw.Draw(picture)
    eps = max(float(np.linalg.norm(hi - lo)) * 0.004, 2.0 / cam.scale)
    for c, _t, _col in scene.meshes:
        draw_edges(draw, scene.lines[c.name], cam, zbuf, eps)
    top = np.array(picture, dtype=float)
    free = np.full((H, W), np.inf)
    if xray:  # screws shown through what hides them
        for c, tris, col in scene.meshes:
            if c.kind == "standard":
                rasterise(tris, np.repeat(col[None, :], len(tris), axis=0), cam, free.copy(), top,
                          depth_test=False, alpha=0.55)
    for _a, _b, _s, tris in scene.shared_meshes:  # overlaps: always seen
        rasterise(tris, np.repeat(np.array(OVERLAP, float)[None, :], len(tris), axis=0), cam, free.copy(), top,
                  depth_test=False, alpha=0.9)
    picture = Image.fromarray(np.clip(top, 0, 255).astype(np.uint8))
    draw = ImageDraw.Draw(picture)
    for _a, _b, s, _t in scene.shared_meshes:
        c = s.BoundBox.Center
        px, py, _ = cam.project(np.array([c.x, c.y, c.z]))
        r = min(max(12.0, s.BoundBox.DiagonalLength * cam.scale / 2 + 6), W / 3)
        draw.ellipse([px - r, py - r, px + r, py + r], outline=OVERLAP, width=2)
    if labels and len(scene.components) > 1:
        seen: set[str] = set()
        for c in scene.components:
            if c.kind == "standard" or c.name in seen or len(scene.components) > 40:
                continue
            seen.add(c.name)
            b = c.shape.BoundBox
            px, py, _ = cam.project(np.array([b.Center.x, b.Center.y, b.ZMax]))
            label(draw, (px - 20, py - 18), c.name, (70, 70, 70), 12)
    label(draw, (16, 12), title, (20, 20, 20), 15)
    if view != "iso":
        bar = nice_length(W * 0.18 / cam.scale)
        x0, y0 = 16, H - 28
        draw.line([(x0, y0), (x0 + bar * cam.scale, y0)], fill=(20, 20, 20), width=3)
        label(draw, (x0, y0 - 20), f"{bar:g} mm", (20, 20, 20), 12)
    else:
        label(draw, (16, H - 30), "x right · y back · z up", (90, 90, 90), 12)
    notes = []
    if xray:
        notes.append(("standard parts, seen through", STANDARD))
    if scene.shared:
        notes.append((f"{len(scene.shared)} overlap(s)", OVERLAP))
    x = W - 16
    for text, colour in reversed(notes):
        w = draw.textlength(text, font=font(12)) + 22
        x -= w
        draw.rectangle([x, H - 28, x + 12, H - 16], fill=colour)
        label(draw, (x + 16, H - 31), text, (20, 20, 20), 12)
        x -= 12
    return picture


def closeup(components: list[Component], box, tol: float, order: dict[str, int], root: Path, out_dir: Path,
            stem: str, title: str, only: tuple[str, ...] = ()) -> str:
    """A 3D close-up of a region, everything outside it cut away, standard parts seen through.
    only: just these components (an overlap's two), so nothing in front hides them."""
    import FreeCAD as App
    import Part

    half = max(25.0, box.DiagonalLength * 1.5)
    c = box.Center
    region = Part.makeBox(2 * half, 2 * half, 2 * half, App.Vector(c.x - half, c.y - half, c.z - half))
    cut = []
    for comp in components:
        if only and comp.name not in only:
            continue
        if not comp.shape.BoundBox.intersect(region.BoundBox):
            continue
        try:
            piece = comp.shape.common(region)
        except Exception:  # noqa: BLE001
            continue
        if not piece.isNull() and piece.Volume > 1e-6:
            cut.append(Component(comp.name, piece))
    scene = Scene(cut, min(tol, max(0.02, half / 400)), order, len(cut) > 1)
    lo = np.array([c.x - half, c.y - half, c.z - half])
    hi = np.array([c.x + half, c.y + half, c.z + half])
    picture = draw_scene(scene, "iso", lo, hi, title, True, labels=True)
    draw = ImageDraw.Draw(picture)
    label(draw, (16, 34), f"region {2 * half:.0f} mm across around x {c.x:.1f}, y {c.y:.1f}, z {c.z:.1f}",
          (90, 90, 90), 12)
    path = out_dir / f"{stem}.png"
    picture.save(path)
    return path.relative_to(root).as_posix()


def render(target: str, root: Path, views: list[str], xray: bool | None, focus: str | None = None) -> dict:
    components = load(target, root)
    name = Path(target).stem
    lo = np.array([min(c.shape.BoundBox.XMin for c in components), min(c.shape.BoundBox.YMin for c in components),
                   min(c.shape.BoundBox.ZMin for c in components)])
    hi = np.array([max(c.shape.BoundBox.XMax for c in components), max(c.shape.BoundBox.YMax for c in components),
                   max(c.shape.BoundBox.ZMax for c in components)])
    diag = float(np.linalg.norm(hi - lo)) or 1.0
    tol = max(0.05, diag * 0.0015)
    assembly = len(components) > 1
    if xray is None:
        xray = assembly and any(c.kind == "standard" for c in components)

    order: dict[str, int] = {}
    scene = Scene(components, tol, order, assembly)

    out_dir = root / "exports" / "renders" / name
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("*.png"):
        old.unlink()
    files = []
    for view in views:
        picture = draw_scene(scene, view, lo, hi, f"{target} · {NAMES[view]}", xray, labels=view == "iso")
        path = out_dir / f"{view}.png"
        picture.save(path)
        files.append(path.relative_to(root).as_posix())

    # close-ups: where things overlap, and what was asked for, cut out of the rest
    regions = []
    if focus:
        hit = [c for c in components if c.name == focus or c.name.split(":")[0] == focus]
        if not hit:
            raise LoadError(f"there is no component '{focus}'; there are: {', '.join(c.name for c in components[:40])}")
        b = hit[0].shape.BoundBox
        regions.append((f"close-up of {hit[0].name}", b, "focus", ()))
    for i, (a, b_, s) in enumerate(scene.shared[:2]):
        regions.append((f"overlap {i + 1}: {a} and {b_}, only these two shown", s.BoundBox, f"overlap-{i + 1}", (a, b_)))
    for title, b, stem, only in regions:
        files.append(closeup(components, b, tol, order, root, out_dir, stem, f"{target} · {title}", only))


    # meshes for the dashboard's 3D preview
    preview = root / "exports" / "preview" / name
    manifest = {"target": target, "components": [], "overlaps": []}
    for i, (c, tris, col) in enumerate(scene.meshes):
        rel = f"{i:03d}.stl"
        write_stl(preview / rel, tris)
        manifest["components"].append({"name": c.name, "kind": c.kind, "file": rel,
                                       "colour": "#%02x%02x%02x" % tuple(int(v) for v in col)})
    for i, (a, b, _s, tris) in enumerate(scene.shared_meshes):
        rel = f"overlap-{i:03d}.stl"
        write_stl(preview / rel, tris)
        manifest["overlaps"].append({"a": a, "b": b, "file": rel})
    (preview / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")

    def box(shape) -> dict:
        b = shape.BoundBox
        return {"x": [round(b.XMin, 2), round(b.XMax, 2)], "y": [round(b.YMin, 2), round(b.YMax, 2)],
                "z": [round(b.ZMin, 2), round(b.ZMax, 2)]}

    summary = {
        "target": target,
        "views": files,
        "size_mm": [round(float(v), 2) for v in hi - lo],
        "components": [{"name": c.name, "kind": c.kind, "box_mm": box(c.shape)} for c in components],
        "overlaps": [{"a": a, "b": b, "volume_mm3": round(s.Volume, 2), "box_mm": box(s)} for a, b, s in scene.shared],
        "preview": (preview / "manifest.json").relative_to(root).as_posix(),
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    return summary


def describe(summary: dict) -> str:
    lines = [f"{summary['target']}: {' x '.join(f'{v:g}' for v in summary['size_mm'])} mm overall, "
             f"{len(summary['components'])} component(s)."]
    if len(summary["components"]) > 1:
        for c in summary["components"][:60]:
            b = c["box_mm"]
            lines.append(f"- {c['name']} ({c['kind']}): x {b['x'][0]}..{b['x'][1]}, y {b['y'][0]}..{b['y'][1]}, "
                         f"z {b['z'][0]}..{b['z'][1]}")
        if len(summary["components"]) > 60:
            lines.append(f"- ... {len(summary['components']) - 60} more")
    if summary["overlaps"]:
        lines.append(f"Overlaps (red in the pictures): {len(summary['overlaps'])}")
        for o in summary["overlaps"][:20]:
            b = o["box_mm"]
            lines.append(f"- {o['a']} and {o['b']}: {o['volume_mm3']} mm³ at x {b['x'][0]}..{b['x'][1]}, "
                         f"y {b['y'][0]}..{b['y'][1]}, z {b['z'][0]}..{b['z'][1]}")
    else:
        lines.append("No overlaps.")
    lines.append("Pictures: " + ", ".join(summary["views"]))
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("target", help="parts/<name>.py, assemblies/<name>.py or reference/<name>.step")
    ap.add_argument("--views", default="iso,front,top,side")
    ap.add_argument("--xray", action=argparse.BooleanOptionalAction, default=None)
    ap.add_argument("--focus", help="also a close-up of this component (a name from the summary)")
    ap.add_argument("--json", action="store_true", help="print the summary as JSON")
    args = ap.parse_args(argv)
    views = [v.strip() for v in args.views.split(",") if v.strip()]
    unknown = [v for v in views if v not in VIEWS]
    if unknown:
        print(f"unknown view(s): {', '.join(unknown)}; there are {', '.join(VIEWS)}", file=sys.stderr)
        return 2
    try:
        summary = render(args.target, Path.cwd(), views, args.xray, args.focus)
    except LoadError as e:
        print(f"can't render {args.target}: {e}", file=sys.stderr)
        return 1
    print(json.dumps({**summary, "text": describe(summary)}) if args.json else describe(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
