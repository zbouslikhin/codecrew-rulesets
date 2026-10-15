# freecad-model

## v1.0.0

The first version: freecad-part slimmed down for modelling sessions, where you decide and one
modeller models a step at a time.

- design/decisions.md holds your decisions; the skill grilling-a-design asks for them before
  the first step and whenever one is missing.
- The render tool: pictures of a part, an assembly or a reference file (3D, front, top, side,
  close-ups of overlaps), for the agent and the dashboard's 3D preview.
- Errors only for what is objectively wrong: invalid solids, larger than the bed, overlaps
  (alike ones grouped into one), too little thread. Sharp edges, overhangs and thin walls are
  warnings.
- standards.shapes.placed_screw: a screw by where its head bears and which way it goes.
- Four skills instead of fourteen; no specs, concept files, process profiles, handover or
  generated drawings.
- A pipeline template, "Modelling session": one modeller, one stage, a commit per step.
