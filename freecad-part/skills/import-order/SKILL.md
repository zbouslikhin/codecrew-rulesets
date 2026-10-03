---
name: import-order
description: The import order and module layout FreeCAD 1.1 needs when it runs headless, and what the errors mean when it's wrong. Read before you write a new part module, test or script.
---
# Import order and module layout

Parts run in FreeCAD's own Python (3.11), headless, in the toolchain image. Two things differ
from ordinary Python.

## FreeCAD before Part

```python
from dataclasses import dataclass

import FreeCAD as App
import Part
```

`import Part` on its own crashes FreeCAD 1.1: Part needs the application initialised, and
importing `FreeCAD` does that. The crash is a segmentation fault or an abort, not a Python
exception, so the checks report it as a failed build without a traceback
(`validate/build-error`, or pytest dying mid-collection).

- Always import `FreeCAD` first, in **every** module that imports Part: parts, tests, scripts.
  A test that imports Part before importing the part module crashes the same way.
- ruff sorts imports alphabetically within a block, and `FreeCAD` sorts before `Part`: keep them
  in the same block and the formatter preserves the order. Don't separate them with a blank line
  or put `Part` in another group.
- Other workbench modules (`Sketcher`, `Draft`, `Mesh`, `Import`) follow the same rule: after
  `FreeCAD`.
- No GUI: `FreeCADGui` isn't available headless. Anything that needs a view (selection in the
  3D view, colours on screen) has no place in a part module.

## What a part module contains

In this order, as the generator writes it (start with the scaffold tool, generator `part`):

1. The docstring: what the part is for, its material, the design decisions a reviewer should know.
2. Imports: `dataclasses`, then `FreeCAD as App` and `Part`.
3. `DENSITY_G_CM3` (optional) and constants like `EPS`.
4. `@dataclass(frozen=True) class Params`: every dimension, named with its unit
   (`width_mm`, `angle_deg`), with its default value.
5. `PARAMS = Params()`, and `PARAM_RANGES` when a dimension can't vary by 10%.
6. Helper functions that take `Params` (positions, selectors).
7. `def build(p: Params = PARAMS) -> Part.Shape`.

Nothing runs at import time except these definitions: no `build()` call at module level, no
document creation, no export. The `validate` check imports the module and calls `build` itself,
several times, with changed parameters.

## Tests and scripts

- `tests/conftest.py` puts the repository root on the path; tests import `from parts import
  <part>` and call `<part>.build()`.
- Run them the way the checks do: `python -B -m pytest -q -p no:cacheprovider`. `-B` matters:
  without it Python may reuse a stale bytecode cache of a part you just edited.
- Exports (STEP, STL) belong in `scripts/export.py` and write to `exports/`, which git ignores.
  A part module never writes files.

## When it still crashes

- **Segfault at import**: an `import Part` (or another workbench) before `FreeCAD`, somewhere in
  the import chain. Search all of `parts/`, `tests/` and `scripts/`.
- **`ModuleNotFoundError: FreeCAD`**: the command ran in another Python than FreeCAD's. Use
  `python` as the toolchain provides it; don't create a virtual environment.
- **`Part.OCCError`** in `build`: real geometry trouble (a fillet too large, a boolean of
  shapes that don't touch). That's the skill `edges-by-geometry`, not the imports.
