---
name: proving-it
description: "Prototype, inspection and testing: what to print, which sizes to measure with which tolerance, which tests prove the high risks. Read at the prototype, inspection and testing stages."
---
# Proving it

## Prototype: design/prototype.toml

Export first (`python -B scripts/export.py`), then:

```toml
material = "~1.4 kg PETG"
time = "~22 h"
[[part]]
name = "slide_bracket"
count = 6
file = "exports/slide_bracket.stl"
prints_on = "its rail face"
[settings]
walls = 4
infill = "40 % gyroid on load parts"
```

Order the queue so the person can assemble while the rest prints.

## Inspection: design/inspection.toml

Only the sizes that matter for fit and strength, five or so. Nominal is what should print
(after the workshop's corrections, the drawn size may differ: say both).

```toml
[[point]]
id = "groove"
name = "Tile: groove for the tongue"
nominal = 1.9
plus = 0.2
minus = 0.1
drawn = 2.2
how = "calipers, inside jaws, at the middle of the seam"
```

codecrew compares the person's measurements with these. For one out of tolerance, say what it
means and what to change; a printer correction goes into design/profile_updates.md.

## Testing: design/tests.toml

One test per high risk that only the whole thing proves:

```toml
[[test]]
id = "load"
name = "20 kg, drawer all the way out, 1 hour"
how = "Load it evenly, pull it out fully, measure the front's drop after an hour."
pass_if = "Drops less than 4 mm, no seam opens."
covers = ["seam", "pullout"]
```

When the person reports, judge each against its pass criterion and report. Don't change the
design here: a failure is decided at the release.
