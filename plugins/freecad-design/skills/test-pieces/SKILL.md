---
name: test-pieces
description: "When a small test print is worth it before the detailed design, and how to write one: what to print, what to do, what passes. Read at the test-pieces stage."
---
# Test pieces

A test piece is a small print that answers one question before the design depends on the
answer. Suggest one only when all four hold:

1. the risk is high or medium;
2. no calculation, datasheet or measurement of a bought part settles it;
3. the workshop (design/workshop.md) doesn't already know the answer, e.g. the printer's
   shrink measured on an earlier project;
4. finding out later costs more than the piece: many parts depend on it, long prints, an order.

Usually that leaves zero to three. Zero is a good answer: say so and why.

## design/test_pieces.toml

```toml
[[piece]]
id = "seam"
question = "Is the seam as stiff as a tile?"
target = "test_pieces/seam.py"
print_time = "25 min"
do = "Support the ends, hang 5 kg in the middle, measure the drop; the same on a piece without the seam."
pass_if = "The seam drops less than twice the plain piece."
risk = "seam"

[[considered]]
risk = "pullout"
reason = "Ruthex's datasheet gives the pull-out for PETG"
```

Model each piece as a part (`PARAMS`, `build`) in test_pieces/, small, with only the feature
under test, and export it: `bash "${CLAUDE_PLUGIN_ROOT}/bin/fc" export test_pieces`.

## Results

The person sends a result per piece, with photos. Say what each means. If a result changes
the concept (a seam bends: more screws, a rib, another split), the parts of the fix that are
on their "decide yourself" list you do; how parts join, what's seen and what's bought you ask.
Measured corrections for their printer or parts go into design/profile_updates.md, one line
each ("K1: grooves print 0.3 mm narrow, holes 0.15 mm small"), and into decisions.md.
