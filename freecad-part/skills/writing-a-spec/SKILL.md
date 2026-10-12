---
name: writing-a-spec
description: How to write a part's or assembly's spec (design/<name>.spec.toml) so the checks can read it. Read before you start a part, or change what one must do.
---
# Writing a spec

A part starts from what it must be, not from its geometry. The spec is that, as data: the checks
read it, measure the built part against it, and refuse a requirement nothing proves. Write it
first, from the request and its sources; then model. Start a new part with the scaffold tool
(generator `part`): it writes the spec's skeleton with the module and the test.

## A part: design/<part>.spec.toml

```toml
kind = "part"
name = "cable_clip"                 # the file's name, and parts/cable_clip.py
purpose = "Holds a 6 mm cable on a 20 x 20 extrusion, snapped on without tools."
quantity = 200                      # how many are made: it decides the process
material = "PETG"
processes = ["fdm"]                 # every process it must be makeable by

[envelope_mm]                       # measured on the built part, in any orientation
x = 26.0
y = 14.0
z = 10.0

[mass_g]                            # optional; needs DENSITY_G_CM3 in the part
max = 5.0

[[sources]]                         # what the design starts from; usually several
kind = "text"
note = "A clip for the sensor cable along the gantry extrusion."

[[sources]]
kind = "cad"                        # CAD it must fit: a file in reference/
ref = "reference/extrusion_2020.step"

[[sources]]
kind = "drawing"                    # or datasheet; a file here, or attachment:<name> of the run
ref = "attachment:clip-sketch.pdf"

[[interfaces]]                      # what it mates with, and the parameters that make it fit
id = "I1"
mates_with = "20 x 20 extrusion slot"
feature = "snap arms"
parameters = ["slot_width_mm", "arm_angle_deg"]
fit = "snap fit, 0.2 mm clearance"

[[requirements]]                    # what must be true, and what proves it
id = "R1"
text = "The cable opening takes a 6 mm cable with 0.4 mm clearance."
proven_by = ["test:test_cable_opening", "param:cable_diameter_mm"]

[[requirements]]
id = "R2"
text = "It fits between the extrusion and the cover."
proven_by = ["check:envelope"]
```

## What proves a requirement

| Proof | Means | Checked |
|---|---|---|
| `test:<function>` | a test in tests/test_<part>.py asserts it | the function exists; pytest runs it |
| `param:<name>` | a parameter of Params is the requirement (a diameter, a spacing) | the parameter exists |
| `check:envelope` | the built part stays within envelope_mm | measured by the validate check |
| `check:mass` | the built part weighs at most mass_g.max | measured by the validate check |
| `check:strength` | every load in `[[loads]]` is carried with its safety factor | calculated by the validate check (skill `checking-strength`) |

Prefer a test: it proves the built geometry. `param:` only proves the number was written down;
use it together with a test when the fit matters. A requirement without `proven_by` fails the
checks: if you can't say what proves it, it isn't a requirement yet. Say so in your open issues.

## Rules that keep a spec useful

- **One requirement, one fact.** "Fits the slot and holds the cable" is two.
- **Numbers with units**, in the text and in the parameters' names.
- **Every interface names its parameters.** That is how a mating dimension stays traceable: when
  the screw changes from M4 to M5, the spec says which parameters move.
- **Envelope from the real constraint** (the space it goes into), not from the part you happen to
  have modelled. If nothing constrains it, give the size you intend and say so in the purpose.
- **A part that mates with nothing** says `standalone = true` instead of interfaces. That is rare.
- **Don't delete a requirement to make the checks pass.** Change it only when the request did.

## An assembly: design/<assembly>.spec.toml

```toml
kind = "assembly"
name = "sensor_mount"
purpose = "The sensor bracket screwed to the frame."

[[parts]]
part = "mounting_bracket"           # a part of this repository, with its own spec
quantity = 1

[[parts]]
standard = "ISO 4762 M4x12"         # a standard part, by its designation
quantity = 2

[[parts]]
reference = "reference/frame.step"  # CAD it must fit

[[joints]]                          # which interface meets which
a = "mounting_bracket:I1"
b = "standard:ISO 4762 M4x12"

[[requirements]]
id = "R1"
text = "The bracket is fixed with two M4 screws."
proven_by = ["part:mounting_bracket:R1"]    # or test:<function> in tests/test_<assembly>.py
```

A joint's ends are `<part>:<interface id>`, `standard:<designation>` or `reference:<file>`. An
interface that no joint uses, in a part that belongs to an assembly, is worth a second look.

## Parts from before specs

A repository that had parts before specs were required lists them in `design/legacy.toml`
(`python .codecrew/rulesets/freecad-part/check_spec.py --grandfather` writes it). For those a
missing spec is a warning. When you change such a part, write its spec and take it off the list.
