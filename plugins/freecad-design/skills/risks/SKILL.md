---
name: risks
description: Design risk stage - what can fail, how bad, and what settles each risk
disable-model-invocation: true
allowed-tools: Bash(bash "${CLAUDE_PLUGIN_ROOT}/bin/fc" *)
---
Stage: Design risk. Load the design-risk skill and follow it.

- Read design/decisions.md (the agreed concept) and design/workshop.md if there is one.
- Write design/risks.toml: what can fail, what happens then, how bad, and what settles it
  (datasheet, calculation, test piece, geometry, inspection, test).
- Show the list as a short table, ask the person to approve or change it. When approved, set
  risk "done" and the next stage "active"; end with: run /clear, then the next command.
