---
name: pieces
description: Test pieces stage - small prints that settle a risk before the full design, only when really needed
disable-model-invocation: true
allowed-tools: Bash(bash "${CLAUDE_PLUGIN_ROOT}/bin/fc" *)
---
Stage: Test pieces. Load the test-pieces skill and follow it.

- Suggest a test piece only when the skill's four conditions all hold. List what you looked at
  and why each wasn't needed; "none needed" is a fine answer (then set the stage "skipped").
- Model each piece in test_pieces/<id>.py, describe it in design/test_pieces.toml (what to do,
  what passes, print time), export with `bash "${CLAUDE_PLUGIN_ROOT}/bin/fc" export test_pieces`.
- When the person reports results, write them to design/results/test_pieces.json, say what they
  mean and change design/decisions.md where they must. Then set the stage "done", the next
  "active"; end with: run /clear, then the next command.
