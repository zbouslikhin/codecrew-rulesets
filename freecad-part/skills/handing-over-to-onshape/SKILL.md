---
name: handing-over-to-onshape
description: How a part proven in FreeCAD is rebuilt in Onshape so it stays the same part (one variable per dimension, features in build() order), what the handover check compares, and what may change in Onshape afterwards. Read before you rebuild a part in Onshape, and when the handover check fails.
---
# Handing a part over to Onshape

The part is designed and proven here, in FreeCAD: every check runs on `parts/<name>.py`. Onshape
is where it's used in assemblies and where people change its dimensions. `design/handover.toml`
names the part that goes to the project's Part Studio:

```toml
part = "mounting_bracket"
```

You rebuild it there. You don't redesign it: its `Params` are the contract.

## Variables first, one per dimension

Before any sketch, create a variable for every numeric field of `Params`:

| In Params | In Onshape |
|---|---|
| `width_mm: float = 40.0` | `#width` = `40 mm` |
| `hole_diameter_mm: float = 4.5` | `#hole_diameter` = `4.5 mm` |
| `arm_angle_deg: float = 30.0` | `#arm_angle` = `30 deg` |
| `rib_count: int = 3` | `#rib_count` = `3` |

- The name is the field's name without its unit suffix.
- The value is a **plain number with its unit**, never a formula. A variable people may change
  must be one that can be read back. If `Params` derives a value from others, derive it in a
  feature's expression (`#depth - 2 * #wall`), not in a variable.
- Every one of them, even those you think nobody will change.

## Features in build() order

Read `build()` and make the same solid, step by step: the same base, the same cuts, the same
fillets, in the same order. Every dimension in a sketch or a feature is an expression of the
variables (see `sketch-dimensions`); a typed-in number is a dimension nobody can change from
the variable table. Name every feature for what it is. Check each feature's status after you
make it (`feature-status`), and mind the units of the API (`api-pitfalls`: metres).

Where FreeCAD selects edges by geometry, select them in Onshape by a query that survives a
change of dimensions, not by picking.

## What the handover check compares

After each pass codecrew records the Part Studio (`design/onshape/features.json`,
`properties.json`) and compares it with the part here:

| Finding | Means | Do |
|---|---|---|
| `variable-missing` | a dimension of Params has no variable | create it, and use it |
| `variable-differs` | a variable's value isn't the part's | set the value here's |
| `variable-not-literal` | a handed-over variable is a formula | make it a plain value |
| `volume-differs` | the two solids' volumes differ by more than 0.1% | a feature is missing, extra, or dimensioned differently: compare with build(), feature by feature |
| `size-differs` | the bounding boxes differ by more than 0.01 mm | as above; often a sketch on the wrong plane or an extrude the wrong way |
| `handover-unverified` | Onshape's measurements couldn't be read | say so in your open issues: without them nothing proves the two are the same |

Equal volume and size with every variable in place is the proof that the part in Onshape is the
part that passed the checks. Don't adjust a variable to make the volume match: find the feature
that differs.

## After it's accepted

The hand-over pipeline's last stage records the Onshape features as accepted
(`design/onshape/handover.lock.json`). From then on:

- **Variable values may change in Onshape.** The *Take changes from Onshape* pipeline writes the
  changed values into `Params` and runs every check on the changed part. The person who changed
  the value gets the answer: it still passes, or it breaks a wall thickness, an envelope, a fit.
  Nobody "fixes" such a failure by itself: it goes to a person.
- **Anything else is drift** (`drift`): a feature added, removed, reordered or re-dimensioned in
  Onshape. It can't be taken back automatically. The change is made in the part here, checked,
  and handed over again.

So in Onshape people turn the knobs the design gives them; the shape itself changes here.
