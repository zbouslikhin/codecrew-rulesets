---
name: start
description: Start a FreeCAD design project here, or adopt the one that's here, and take the brief
disable-model-invocation: true
allowed-tools: Bash(bash "${CLAUDE_PLUGIN_ROOT}/bin/fc" *)
argument-hint: "[what to design]"
---
Set this folder up as a FreeCAD design project, then take the brief.

1. Run `bash "${CLAUDE_PLUGIN_ROOT}/bin/fc" setup`. If FreeCAD or Pillow is
   missing, stop and tell the person what to install (`setup --install` adds ruff, pytest,
   Pillow to FreeCAD's Python).
2. Run `bash "${CLAUDE_PLUGIN_ROOT}/bin/fc" new`. In an existing project it only adds what's missing (CLAUDE.md,
   design/flow.toml, the export script); nothing is overwritten.
3. If design/flow.toml is new and the project already has work in it (decisions, concepts,
   parts, a plan), set each stage's status in design/flow.toml from what's there, and say what
   you set.
4. The brief: what is being designed ($ARGUMENTS, or ask), how much is at stake (level 1-4 in
   design/flow.toml), and the printer (design/printer.toml: name and bed size). Ask whatever the
   person hasn't said with one AskUserQuestion call. Mark stages the level doesn't need "off":
   level 1 needs no concept, risk, test pieces, analysis or testing.
5. Put everything the person already knows into design/decisions.md (their words, one line
   each), set grilling to "active", and end with: run /clear, then /freecad-design:grill.
