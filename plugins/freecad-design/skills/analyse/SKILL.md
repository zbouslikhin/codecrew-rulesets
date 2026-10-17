---
name: analyse
description: Analysis and DFM stage - hand calculations as scripts, and the print table
disable-model-invocation: true
allowed-tools: Bash(bash "${CLAUDE_PLUGIN_ROOT}/bin/fc" *)
---
Stage: Analysis and DFM. Load the analysis skill and follow it.

- Calculate what design/risks.toml says a calculation settles: one script per result in
  analysis/, each reading the parts' PARAMS and printing one JSON line. Run them all with
  `bash "${CLAUDE_PLUGIN_ROOT}/bin/fc" analysis`.
- A result that fails: say why and propose the change; make it only when the person agrees.
- Write design/analysis.toml (results, the print table: part, count, face on the bed, fits,
  supports) and update design/risks.toml. Set analysis "done" and the next stage "active"; end
  with: run /clear, then the next command.
