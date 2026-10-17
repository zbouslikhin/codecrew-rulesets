---
name: plan
description: Plan stage - the detailed design as small steps with milestones
disable-model-invocation: true
allowed-tools: Bash(bash "${CLAUDE_PLUGIN_ROOT}/bin/fc" *)
---
Stage: Plan. Load the planning-the-detail skill and follow it.

- Write design/plan.toml: one part, one joint or one assembly per step, in an order that
  builds on what exists (references first), with milestone = true where the person must look
  before it goes on (the first assembly, the parts you see, the full assembly).
- Before you finish, list every decision a step will need that design/decisions.md doesn't
  have, and ask them now (AskUserQuestion), so the CAD stage can run without stopping.
- When the person approves, set plan "done" and cad "active"; end with: run /clear, then
  /freecad-design:cad.
