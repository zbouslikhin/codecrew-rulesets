---
name: analysis
description: "How to check the detailed design with numbers: hand calculations as scripts that read the model, and the print table. Read at the analysis stage."
---
# Analysis and DFM

Calculate what design/risks.toml says a calculation settles. Each calculation is a script, so
it runs again when the model changes and the reviewer can rerun it.

## analysis/<name>.py

Reads its numbers from the parts' PARAMS and design/results/ (measured values beat
assumptions), prints one JSON line:

```json
{"id": "floor_sag", "name": "Front drop at full extension", "value": 3.3, "limit": 4.0, "unit": "mm", "ok": true, "inputs": "3 mm floor + rib, seam stiffness from test piece 3"}
```

Use a margin of at least 2 on strength for printed parts; halve a datasheet value for loads
across the layers. When a number isn't known well enough, don't calculate: say a test proves
it.

## design/analysis.toml

```toml
[[result]]
id = "floor_sag"
name = "Front drop at full extension"
value = 3.3
limit = 4.0
unit = "mm"
ok = true
script = "analysis/floor_sag.py"

[[print]]
part = "tray_tile"
count = 10
prints_on = "its floor"
fits = true
supports = "none"

[[fixed]]
what = "Grip slot roof at 60°"
change = "a 45° teardrop"
```

Then update design/risks.toml with what the detail added.
