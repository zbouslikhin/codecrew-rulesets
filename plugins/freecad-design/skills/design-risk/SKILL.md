---
name: design-risk
description: "How to list what can fail in a design, how bad it would be, and what settles each risk: a design choice, a calculation, a datasheet, a measurement, a test piece or a test. Read at the design-risk stage, and again when the detailed design adds something risky."
---
# Design risk

Find the risks while the layout can still change cheaply. For each, decide what settles it.
The level decides how deep: level 1 has no risk list; level 2 lists what can break, fall or
wear; levels 3 and 4 go through every part and every joint.

## design/risks.toml

```toml
[[risk]]
id = "seam"
what = "The long seam across the depth flexes"
then = "The floor sags at full extension; the drawer scrapes the rails"
severity = "high"            # high: someone or something gets hurt or broken; medium: it stops working well; low: it looks wrong
settle = "test piece"        # design | calculation | datasheet | measure | geometry | test piece | test
cover = "Tongue and groove and an M4 per seam"
proved_in = "test piece 3, then test 1"
```

## What settles a risk

- **design**: a choice that removes it (a rib, a stop, a different split).
- **calculation**: a hand calculation the analysis stage will do (bending, pull-out, sag).
- **datasheet**: a bought part's published number (a slide's load rating, an insert's
  pull-out).
- **measure**: the person measures a bought part they have.
- **geometry**: the model shows it (clearances, overlaps).
- **test piece**: nothing above settles it and it would be costly to find out later.
- **test**: only the whole thing shows it (cycling, vibration, wear).

Say honestly when something can't be calculated: a T-nut's grip on a rail is a test, not a
formula.
