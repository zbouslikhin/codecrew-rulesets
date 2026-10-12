# {{name}}

Parametric parts, scripted in Python with FreeCAD. Every part in `parts/` has its
dimensions in a `PARAMS` dataclass (each named with its unit) and a `build()` that returns
the shape; `tests/` checks what matters about each part.

    make check PROJECT={{name}}        # the rules the agents are held to
    python scripts/export.py           # exports/<part>.step and .stl (FreeCAD's Python)

## Specs

Every part starts from `design/<part>.spec.toml`: what it is for, the material and process, the
envelope and mass it must stay within, its interfaces and its requirements, each with what
proves it. Assemblies have one too. The checks read these files; see the skill `writing-a-spec`.
