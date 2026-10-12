---
name: engineering-workflow
description: The order a mechanical design is worked in here, from spec to deliverables, and which skill to load at which step. Read first, before any other skill, when you start on a part or an assembly.
---
# The engineering workflow

Work in this order. Each step has checks behind it, so skipping one comes back as a failed
check later, when it costs more to fix.

| Step | You do | Load the skill | The checks then hold you to |
|---|---|---|---|
| 1. Requirements | Write or read the spec: purpose, quantity, material, process, envelope, mass, sources, appearance | `writing-a-spec` | a complete spec; a material and process that suit each other |
| 2. Interfaces | Say what it mates with, name the dimensions that make it fit, and tolerance them | `choosing-a-fit`, `choosing-a-fastener` | every interface realised by a toleranced parameter; standards for threads |
| 3. Concept | Decide the shape for the process, before any geometry | `designing-for-a-process`, `designing-for-people` | (nothing yet: this is where a wrong process is cheap to fix) |
| 3a. Loads | If it carries a force, flexes or snaps: state the load cases and the safety factor, and size the sections for them | `checking-strength` | every load carried with its safety factor, within its deflection |
| 4. Parameters | Put every dimension in `Params`, named with its unit, standard sizes from the library | `standard-sizes` | units in names; standard values or a stated reason |
| 5. Geometry | Model: the interfaces first, then the body, then the details; edge breaks last | `import-order`, `edges-by-geometry` | a valid solid that survives every dimension changing by 10% |
| 6. Make it makeable | Read the manufacturability findings and fix the design, not the limits | `designing-for-a-process` | walls, holes, corners, overhangs, draft, reach, for every process named |
| 7. Prove it | A test for each requirement that a test can prove | `writing-a-spec` | every requirement proven; envelope and mass measured |
| 8. Assemble | Place the parts by their interfaces; state fits and stacks | `placing-an-assembly`, `choosing-a-fit` | no interference; joints meeting; screws engaged and reachable; fits and stacks in the worst case |
| 9. Hand over | Nothing: codecrew generates the drawing, views, report and bill of materials | `deliverables` | (generated; read the report as your reviewer will) |

## If the spec is already there

A spec with `status = "proposed"` was written and approved before you: it is the contract.
Build to it, name parameters and tests as it names them, and remove the `status` line from a
spec when you build its part (the check insists). Don't change a requirement, a tolerance, the
material or the process to make a check pass. If the spec can't be met, or is wrong, say so in
your open issues with the numbers: changing it is the human's decision.

If there is no spec, write it first (step 1), in the same pass. Never model first and write the
spec to match.

## Before you finish

Read `deliverables/<name>/report.md` as the reviewer will: does every requirement have evidence
that actually proves it, are the manufacturability sections free of findings, is anything left
"none" that shouldn't be? What the checks can't decide (a requirement the request left open, a
limit that seems wrong for this shop, a form that works but looks awkward) goes into your open
issues, plainly.
