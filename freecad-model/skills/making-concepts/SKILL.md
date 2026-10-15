---
name: making-concepts
description: "How to show the person two or three concepts as block models at real size, rendered in place, so they agree on the design before any detail. Read at the concept stage."
---
# Making concepts

A concept answers "what will it look like and where does everything go", not "how is it
built". The person agrees on it from the renders, so it must be honest: real sizes, real
clearances, in the real surroundings.

## What a concept is

- `concepts/<id>.py` with `build()` returning `{name: Part.Shape}` like an assembly: the
  reference geometry (the frame, what exists) plus block models of the new parts.
- Blocks only: boxes and cylinders at their outer size. No holes, inserts, fillets or screws.
  Where parts split (for the bed, for a seam), show the split as a gap of 0.5 mm.
- Every size comes from design/decisions.md or the reference: a size you invent is a decision.
- Ids are letters: `a`, `b`, `c`.

## How many, and how they differ

Make 2 or 3, and only where the person's answers leave room: the front's style, where seams
go, a handle or a grip, what's printed and what's bought. Don't vary what they decided. If
nothing is left open, make one and say so.

## Render and describe

Render each with views `iso,front,top` (and `side` when depth matters). Then write
design/concepts.toml:

```toml
[[concept]]
id = "b"
name = "Flush, cover strips"
target = "concepts/b.py"
summary = "Front 1021 wide between the posts, 4 mm strips over the 4 seams, grip slot."
differs = ["cover strips over the seams", "4 more small parts"]
clearances = ["overhang: 6 mm", "knees: 610 mm under the drawer"]
```

When the person mixes ("B with C's handle"), build that as a new concept and render it.
When they agree, the next stage writes it into their decisions.
