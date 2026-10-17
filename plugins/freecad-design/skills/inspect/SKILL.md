---
name: inspect
description: Inspection stage - the few sizes to measure on the prototype, and what each measurement means
disable-model-invocation: true
allowed-tools: Bash(bash "${CLAUDE_PLUGIN_ROOT}/bin/fc" *)
---
Stage: Inspection. Load the proving-it skill (the inspection part).

- Write design/inspection.toml if it isn't there: only the sizes that matter for fit and
  strength, each with nominal, plus/minus and how to measure it.
- Ask the person for their measurements (they can type them all in one message). Write them to
  design/results/inspection.json with, for each, the allowed range and whether it's within.
- Out of tolerance: say what it means and what to change (a printer correction goes into
  design/workshop.md). Don't change the design here. Set inspection "done" and the next stage
  "active"; end with: run /clear, then the next command.
