# A FreeCAD design project

Parametric parts in FreeCAD 1.1's Python (Part workbench), designed with the person one step at
a time. They decide; you model, check, render and show. The freecad-design plugin gives you:

- the stage commands, in order: /freecad-design:grill, concept, risks, pieces, plan, cad,
  analyse, prototype, inspect, test, release. /freecad-design:status says where the design is
  (design/flow.toml);
- the tools, run through its `fc` command (the session start tells you its path): check,
  render, export, analysis. The checks also run by themselves after each edit and before you
  finish a turn.

Rules:
- design/decisions.md holds the person's decisions. Read it before every step. What it doesn't
  decide, you don't either: ask (AskUserQuestion, 2-4 options, your recommendation first).
  Write into decisions.md only what the person answered, or mark it "(assumed)".
- parts/<name>.py: PARAMS (a frozen dataclass, every size named with its unit: width_mm) and
  build(params) returning a Part.Shape. Optional: PRINTED = False, RESTS_ON = "-z" (the face on
  the bed), DENSITY_G_CM3. assemblies/<name>.py: build() returns {name: shape} in place:
  "<part>" or "<part>:<n>"; screws "standard:ISO 4762 M3x12:<n>"; reference/<name>.step by name.
- Sizes come from the standards library (standards/fasteners.py etc.), not from memory.
- Import FreeCAD before Part. Select edges and faces by geometry, never by index.
- After a change to geometry: render it and look at the picture before you say it's done.
- Errors stop a step (doesn't build, too large for the bed, overlap, too little thread).
  Warnings (sharp edges, overhangs) are for the person: name them, don't chase them.
- Keep the conversation small: one stage per conversation (the person runs /clear between
  stages), read only the files a step needs, render only when geometry changed.
