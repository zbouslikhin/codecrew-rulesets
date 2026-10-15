# fixture

Parametric parts, modelled with FreeCAD in a codecrew modelling session.

- `design/decisions.md`: your decisions. The modeller reads them every step and never changes
  them on its own.
- `design/printer.toml`: your printer's bed, `bed_mm = [x, y, z]`.
- `parts/`: one module per part. `assemblies/`: one module per assembly.
- `reference/`: what exists and the design must fit, as STEP files.

Pictures of anything modelled:

    python -B .codecrew/rulesets/freecad-model/render.py parts/<name>.py

Exports for printing (STL and STEP into exports/):

    python -B scripts/export.py
