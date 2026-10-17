---
name: test
description: Testing stage - the tests only the whole thing proves; judge the person's results
disable-model-invocation: true
allowed-tools: Bash(bash "${CLAUDE_PLUGIN_ROOT}/bin/fc" *)
---
Stage: Testing. Load the proving-it skill (the testing part).

- Write design/tests.toml if it isn't there: one test per high risk only a test proves, with how
  to do it and what passes.
- When the person reports, write design/results/testing.json and judge each against its pass
  criterion. Don't fix anything here: what to do about a failure is decided at the release.
  Set testing "done" and release "active"; end with: run /clear, then /freecad-design:release.
