---
name: checking-strength
description: How to state what a part must carry (load cases with a safety factor) so the checks calculate it by hand on the part's parameters, which model fits which situation, and what these calculations do not cover. Read when a part carries a force, flexes, snaps, or holds something that matters.
---
# Checking strength

A part that carries something says so in its spec, as load cases. The checks then calculate
each one on the part's parameters, every time the part changes, and hold it to its safety
factor. These are the hand calculations an engineer does first: they tell you whether a
section is in the right range, not whether the part is safe.

## Stating a load

```toml
safety_factor = 2.0          # how many times each load the part must take

[[loads]]
id = "L1"
text = "The sensor's weight in a 5 g shock, at the top of the wall"
model = "cantilever"
force_n = 15.0
length = "height_mm"                                   # a parameter of Params, never a number
section = { shape = "rectangle", width = "width_mm", height = "thickness_mm" }
max_deflection_mm = 1.0                                # optional: how far it may move
stress_concentration = 1.5                             # optional: a hole, a notch, a sharp corner

[[requirements]]
id = "R4"
text = "It carries the sensor without yielding."
proven_by = ["check:strength"]
```

Say in `text` where the force comes from and how you arrived at it (a mass times an
acceleration, a hand pulling, a datasheet). A force nobody can trace is a guess.

## Which model

| Model | Situation | Takes |
|---|---|---|
| `cantilever` | fixed at one end, the force across the other: a bracket's wall, an arm, a tab | `force_n`, `length`, `section` |
| `simply_supported` | resting on two supports, the force in the middle: a shelf, a bridge between two bosses | `force_n`, `span`, `section` |
| `tension` | pulled or pushed along its axis: a strap, a link, a short post | `force_n`, `section` |
| `screws_in_shear` | screws loaded across their axis | `force_n`, `thread`, `count`, `planes`, `property_class` (default "8.8") |
| `snap_arm` | a straight snap arm pushed aside to snap in | `deflection`, `length`, `thickness`; `repeated = true` if opened often |

A section is `{ shape = "rectangle", width, height }`, `{ shape = "round", diameter }` or
`{ shape = "tube", outer, inner }`. For a rectangle, **height is the side along the load**: the
one that resists the bending. Getting it the wrong way round is the usual mistake; a 40 x 3 mm
wall pushed flat-on has height 3, not 40.

Choose the model on the safe side: take the full length to where the force acts, the smallest
section along the member, the worst direction.

## What decides the result

- **Stress** goes with the section's depth squared, **stiffness** with its depth cubed. To
  carry more, deepen the section along the load or add a rib; more width helps only linearly.
- **Allowed stress** is the material's strength from `standards.materials`, times the process's
  `strength_factor` (`processes.toml`): 0.5 for FDM, because a print is weak across its layers.
  Lay a loaded printed part so the load runs along the layers, and if your printer does
  better, the project sets its own factor in `design/processes.toml`.
- **A snap arm** is judged by strain, 1.5 x thickness x deflection / length²: make it longer or
  thinner, not thicker. Print it lying flat, so it bends along its layers.
- **Screws in shear** are the fallback. Prefer a joint where friction, a shoulder or a dowel
  takes the load across.

In your own tests and parts you can use the same formulas: `from standards import strength`.

## What it does not cover

Say these in your open issues when they apply; the checks can't.

- Shapes that aren't a straight member of constant section: plates, shells, short stubby
  parts, anything curved. The model will give a number, and it will be wrong.
- The stress around holes, notches and corners, unless you give `stress_concentration`.
- Fatigue (loads that repeat thousands of times), creep (plastics under a load that stays),
  heat, impact, buckling of thin members in compression.
- Whether the force in the spec is the right one.

A part whose failure would hurt someone, or cost more than the analysis, is analysed and
tested properly. These calculations are for not being surprised.

## Codes

| Code | Means | Do |
|---|---|---|
| `overstressed` | the stress exceeds what is allowed over the safety factor | deepen the section, shorten the arm, stronger material |
| `too-flexible` | it moves more than `max_deflection_mm` | deepen the section, add a rib |
| `overstrained` | a snap arm is strained beyond what the material permits | longer or thinner arm, shallower hook |
| `screw-overloaded` | the screws shear | more, larger or stronger screws; take the shear another way |
| `unknown-load-model`, `spec-incomplete`, `spec-invalid` | the load is written wrongly | see the message |

Never lower a force, a safety factor or a `strength_factor` to make a check pass. If the
requirement is wrong, say so in your open issues: a person decides.
