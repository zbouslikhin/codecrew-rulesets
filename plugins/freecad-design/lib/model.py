"""Loading what the project models: a part, an assembly or a reference file, as named shapes.

    parts/<name>.py        PARAMS and build(params) -> Part.Shape: one component, "<name>"
    assemblies/<name>.py   build() -> {name: Part.Shape}, each already in place
    reference/<name>.step  existing CAD the design must fit: one component, "<name>"

Component names in an assembly: "<part>" or "<part>:<n>" for a part, "standard:<designation>:<n>"
for a standard part (a screw), the reference file's name for a reference.
"""

from __future__ import annotations

import importlib.util
import math
import sys
from dataclasses import dataclass
from pathlib import Path

import FreeCAD  # noqa: F401  must come before Part: `import Part` alone crashes FreeCAD 1.1
import Part


class LoadError(Exception):
    """The target couldn't be built; the message says why, for the agent."""


@dataclass
class Component:
    name: str
    shape: Part.Shape

    @property
    def kind(self) -> str:
        if self.name.startswith("standard:"):
            return "standard"
        if self.name.split(":")[0] in REFERENCES:
            return "reference"
        return "part"


REFERENCES: set[str] = set()  # names of reference files, filled by load()


def _module(path: Path, root: Path):
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    spec = importlib.util.spec_from_file_location(f"{path.parent.name}_{path.stem}", path)
    if spec is None or spec.loader is None:
        raise LoadError(f"{path} isn't a Python module")
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as e:  # noqa: BLE001
        raise LoadError(f"importing {path.name} fails: {type(e).__name__}: {e}") from e
    return module


def read_step(path: Path) -> Part.Shape:
    shape = Part.Shape()
    try:
        shape.read(str(path))
    except Exception as e:  # noqa: BLE001
        raise LoadError(f"reading {path.name} fails: {e}") from e
    return shape


def load(target: str, root: Path) -> list[Component]:
    """The components of a part, an assembly or a reference file, by its repo-relative path."""
    root = root.resolve()
    for ref in (root / "reference").glob("*.st*p"):
        REFERENCES.add(ref.stem)
    path = (root / target).resolve()
    if not path.is_file():
        raise LoadError(f"there is no {target}")
    if path.suffix.lower() in (".step", ".stp"):
        return [Component(path.stem, read_step(path))]
    module = _module(path, root)
    build = getattr(module, "build", None)
    if not callable(build):
        raise LoadError(f"{target} has no build()")
    try:
        if path.parent.name == "parts":
            params = getattr(module, "PARAMS", None)
            built = build(params) if params is not None else build()
        else:
            built = build()
    except Exception as e:  # noqa: BLE001
        raise LoadError(f"build() fails: {type(e).__name__}: {e}") from e
    if isinstance(built, Part.Shape):
        return [Component(path.stem, built)]
    if isinstance(built, dict) and built and all(isinstance(v, Part.Shape) for v in built.values()):
        return [Component(str(k), v) for k, v in built.items()]
    raise LoadError(
        f"build() returned {type(built).__name__}: a part returns a Part.Shape, an assembly a dict "
        "of name -> Part.Shape"
    )


def screw_of(name: str):
    """The standard screw a component is ("standard:ISO 4762 M3x12:1"), or None."""
    if not name.startswith("standard:"):
        return None
    try:
        from standards import fasteners
    except ImportError:
        return None
    found = fasteners.parse(name.split(":")[1])
    return found if found is not None and found.kind == "screw" and found.length_mm else None


def within_shank(screw: Part.Shape, shared: Part.Shape, d: float) -> bool:
    """The shared space lies around the screw's shank, inside its diameter: a thread in a tapped
    hole. A head buried in a part is outside it."""
    cylinders = [f for f in screw.Faces if isinstance(f.Surface, Part.Cylinder)]
    if not cylinders:
        return False
    shank = min(cylinders, key=lambda f: f.Surface.Radius).Surface
    axis, centre = shank.Axis, shank.Center
    for v in shared.Vertexes:
        rel = v.Point - centre
        if (rel - axis * rel.dot(axis)).Length > d / 2 + 0.05:
            return False
    return True


def thread_mm(screw: Component, shared: Part.Shape) -> float | None:
    """How much thread a screw has in what it overlaps, when the overlap is a tapped hole's
    thread (modelled at the tap drill's diameter); None when it's a real overlap."""
    std = screw_of(screw.name)
    if std is None:
        return None
    from standards import fasteners

    d, core = fasteners.diameter(std.thread), fasteners.tap_drill(std.thread)
    per_mm = math.pi / 4 * (d * d - core * core)
    if shared.Volume <= per_mm * std.length_mm * 1.02 + 1e-3 and within_shank(screw.shape, shared, d):
        return shared.Volume / per_mm
    return None


def overlaps(
    components: list[Component], min_mm3: float = 1e-3, threads: dict[str, float] | None = None
) -> list[tuple[str, str, Part.Shape]]:
    """Pairs of components that share space: (a, b, the shared solid). A screw's thread in a
    tapped hole isn't an overlap: its length goes into `threads` (screw name -> mm)."""
    found = []
    for i, a in enumerate(components):
        for b in components[i + 1 :]:
            if not a.shape.BoundBox.intersect(b.shape.BoundBox):
                continue
            try:
                shared = a.shape.common(b.shape)
            except Exception:  # noqa: BLE001
                continue
            if shared.isNull() or shared.Volume <= min_mm3:
                continue
            screws = [c for c in (a, b) if screw_of(c.name)]
            if len(screws) == 1:
                mm = thread_mm(screws[0], shared)
                if mm is not None:
                    if threads is not None:
                        threads[screws[0].name] = threads.get(screws[0].name, 0.0) + mm
                    continue
            found.append((a.name, b.name, shared))
    return found
