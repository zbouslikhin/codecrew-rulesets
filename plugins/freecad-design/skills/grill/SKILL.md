---
name: grill
description: Grilling stage - ask everything the design needs before modelling, in rounds
disable-model-invocation: true
allowed-tools: Bash(bash "${CLAUDE_PLUGIN_ROOT}/bin/fc" *)
---
Stage: Grilling. Load the grilling-a-design skill and follow it.

- Read design/decisions.md and design/flow.toml first; don't ask what's already decided.
- Ask in rounds with AskUserQuestion: up to 4 questions per call, each with 2-4 options, your
  recommendation first (say why in its description). The person can always type their own
  answer or attach a photo in the chat.
- Before each round, say in one line: how many decisions this design needs at its level, how
  many are settled, and roughly how many rounds are left.
- Write every answer into design/decisions.md as it comes.
- When nothing is open (or the person says "take your recommendations": write those in, marked
  "(assumed)"), give a short summary: decided, assumed, still to measure. Set grilling "done"
  in design/flow.toml and the next stage that isn't "off" to "active", and end with: run /clear,
  then the next command.
