---
name: deliverables
description: What codecrew generates for every part and assembly (drawing, design report, bill of materials), where their content comes from, and how a project states its rates for the cost estimate. Read when a drawing or report looks wrong, or when asked about cost.
---
# Deliverables

`deliverables/` is generated from the specs and the built geometry. You never write or edit it,
and you don't list it in a plan. codecrew regenerates what changed before the checks run and
commits it with your work, so the pull request shows the drawing and the report.

| File | For | Contains |
|---|---|---|
| `deliverables/<part>/drawing.svg` | whoever makes it | front, top, right and isometric views with hidden lines; the critical dimensions with tolerance and limits; material, process, general tolerance, mass, envelope, scale |
| `deliverables/<part>/report.md` | whoever reviews it | every requirement with its evidence; interfaces; critical dimensions; manufacturability per process; cost |
| `deliverables/<assembly>/bom.csv` | whoever buys | parts, standard parts and reference parts with quantity, material, process and mass |
| `deliverables/<assembly>/report.md` | whoever reviews it | the bill of materials; each joint's fit and each stack in the worst case; requirements with evidence |

## If a deliverable looks wrong, fix its source

- **A dimension is missing from the drawing.** Critical dimensions are the parameters an interface
  names, those in `[[standards]]` and `[[tolerances]]`, and those that prove a requirement
  (`param:`). Add the parameter to the spec where it belongs; don't draw it.
- **A dimension has no tolerance.** Give it one in the spec, or give the spec a
  `general_tolerance`. A critical dimension without either fails (`dimension-untoleranced`).
- **The evidence for a requirement is thin.** Its `proven_by` is: a test is stronger evidence
  than a parameter.
- **The views don't show a feature.** The four views are fixed. Say so in your open issues if a
  section or detail view is needed: that's a drawing a person makes.

To see them yourself: `python .codecrew/rulesets/freecad-part/deliverables.py` (add `--force` to
rebuild all).

## Cost

A report estimates cost only from the project's own rates, in `design/costs.toml`. Without
rates for the part's material and process it says so; prices are never guessed. Don't invent
rates: if the file is missing and cost matters to the task, name that in your open issues.

```toml
currency = "EUR"

[materials]                # per kg
PETG = 25.0
"Aluminium 6061-T6" = 6.0

[processes.fdm]
rate_per_hour = 4.0        # machine and attention
cm3_per_hour = 15.0        # how fast it builds (or, cut from a block, removes)
setup_minutes = 10         # per batch, shared by the spec's quantity
waste = 0.05               # material bought beyond the part's volume

[processes.milling]
stock = "block"            # material is a block the size of the envelope; the rest is cut away
rate_per_hour = 60.0
cm3_per_hour = 300.0
setup_minutes = 45

[processes.injection_moulding]
rate_per_hour = 40.0
cm3_per_hour = 4000.0
setup_minutes = 120
tooling = 8000.0           # one-off, shared by the quantity
```

The estimate is material plus machine time plus the shares of setup and tooling, each shown with
its arithmetic. It compares designs, processes and quantities; it isn't a quotation.
