---
name: status
description: Where the design is - stages done and next, and what's open
disable-model-invocation: true
allowed-tools: Bash(bash "${CLAUDE_PLUGIN_ROOT}/bin/fc" *)
---
Run `bash "${CLAUDE_PLUGIN_ROOT}/bin/fc" status` and show it. Then, from design/decisions.md and design/plan.toml, add in
three lines at most: the open "(assumed)" decisions, the CAD steps left, and the next command.
