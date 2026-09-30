# fixture-parts

Parametric parts, scripted in Python with FreeCAD. Every part in `parts/` has its
dimensions in a `PARAMS` dataclass (each named with its unit) and a `build()` that returns
the shape; `tests/` checks what matters about each part.

    make check PROJECT=fixture-parts        # the rules the agents are held to
    python scripts/export.py           # exports/<part>.step and .stl (FreeCAD's Python)
