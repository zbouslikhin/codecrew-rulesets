---
name: release
description: Release stage - decide about any failed test, then the print pack
disable-model-invocation: true
allowed-tools: Bash(bash "${CLAUDE_PLUGIN_ROOT}/bin/fc" *)
---
Stage: Release. Load the releasing skill and follow it.

- If design/results/testing.json has a failure, ask first (AskUserQuestion): a revision (what
  to change; cad, then only the failed tests, run again: set those stages "active"/"todo") or
  release as it is with the known issue written down.
- The pack: `bash "${CLAUDE_PLUGIN_ROOT}/bin/fc" export`, then design/release.toml (print, buy, assemble, what was
  proved and how, what wasn't). Commit and tag it (`git tag rev-A`, or the next letter).
  Set release "done".
