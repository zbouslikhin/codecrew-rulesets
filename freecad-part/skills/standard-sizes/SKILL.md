---
name: standard-sizes
description: Which dimensions should be standard sizes (sheet thicknesses, radii, drilled holes, preferred numbers), which materials exist, and how to declare them in the spec. Read when you choose a thickness, a radius, a hole size or a material.
---
# Standard sizes and materials

A dimension that matches what stock and tools come in can be bought and cut; one that doesn't
needs a special. Take these from `standards.sizes` and `standards.materials`.

## Sizes

| Kind in the spec | What it is | Values |
|---|---|---|
| `sheet_thickness` | sheet and plate as stocked | 0.5, 0.8, 1, 1.2, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10, 12, 15, 20 mm |
| `radius` | fillets and bends (DIN 250) | 0.2, 0.3, 0.4, 0.5, 0.6, 0.8, 1, 1.2, 1.6, 2, 2.5, 3, 4, 5, 6, 8, 10, 12, 16, 20, 25 mm |
| `drill` | a drilled hole | 0.1 mm steps up to 10 mm, 0.5 mm steps above |
| `preferred` | any free dimension (ISO 3, R20) | 1, 1.12, 1.25, 1.4, 1.6, 1.8, 2, 2.24, 2.5, 2.8, 3.15, 3.55, 4, 4.5, 5, 5.6, 6.3, 7.1, 8, 9 and their decades |

Declare the parameters that should follow one:

```toml
[[standards]]
parameter = "thickness_mm"
standard = "sheet_thickness"

[[standards]]
parameter = "fillet_radius_mm"
standard = "radius"
```

The check compares the parameter's value in PARAMS with the table and names the nearest standard
values when it isn't one. A deliberate exception states its reason in the entry
(`reason = "..."`).

What to declare: the thickness of anything cut from sheet or plate; radii a cutter or a bending
tool makes; drilled holes; and dimensions nothing else constrains (prefer a preferred number to
37.3). What not to declare: dimensions fixed by what the part mates with (those belong to an
interface) and dimensions a printer makes as easily as any other.

Keep derived geometry within the standard too: if a fillet is limited to the room it has
(`min(p.fillet_radius_mm, ...)`), the parameter still states the standard radius you intend.

## Materials

The spec's `material` must be a name from `standards.materials.MATERIALS`, and each of its
`processes` must suit that material, or the spec check fails (`unknown-material`,
`material-process`).

```python
from standards import materials
materials.get("PETG").density_g_cm3      # 1.27
materials.get("PETG").processes          # ("fdm",)
```

Plastics: PLA, PETG, ABS, ASA, PA12, PC, PP, POM, standard resin. Metals: Aluminium 6061-T6,
5052-H32 and 7075-T6; Steel S235JR and S355J2; Stainless 1.4301 (304) and 1.4404 (316L); Brass
CW614N.

The part's mass is worked out from the material's density: a part doesn't need its own
`DENSITY_G_CM3`, and one that disagrees with its material fails (`density-mismatch`).

If the right material isn't in the library, don't pick the nearest name: say so in your open
issues. It's added to the ruleset, not to the project.
