---
name: concept
description: Concept stage - two or three block models at real size to agree on before detailing
disable-model-invocation: true
allowed-tools: Bash(bash "${CLAUDE_PLUGIN_ROOT}/bin/fc" *)
---
Stage: Concept. Load the making-concepts skill and follow it.

- Build 2 or 3 concepts only where the decisions leave room: block models at real size in
  concepts/<id>.py, render each (`bash "${CLAUDE_PLUGIN_ROOT}/bin/fc" render concepts/<id>.py --views iso,front,top`),
  look at the pictures, and describe them in design/concepts.toml.
- Show them to the person: what differs, what each costs or gains. Ask which they agree on
  (AskUserQuestion, plus "mix them, in my words").
- When they agree, write the agreed concept into design/decisions.md under "## Concept, agreed"
  (outer sizes, splits, front, clearances). Set concept "done" and the next stage "active" in
  design/flow.toml; end with: run /clear, then the next command.
