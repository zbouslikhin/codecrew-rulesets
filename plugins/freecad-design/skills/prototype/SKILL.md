---
name: prototype
description: Prototype stage - export the print files and write the print queue
disable-model-invocation: true
allowed-tools: Bash(bash "${CLAUDE_PLUGIN_ROOT}/bin/fc" *)
---
Stage: Prototype. Load the proving-it skill (the prototype part).

- `bash "${CLAUDE_PLUGIN_ROOT}/bin/fc" export` writes exports/<part>.stl, each turned onto the face it prints on, and
  .step files.
- Write design/prototype.toml (what to print, how many, which face down, settings, roughly how
  much filament and time) and design/build.md (what to buy, cut, print, and the assembly order).
- Tell the person where the files are. When they say it's printed, set prototype "done" and the
  next stage "active"; end with: run /clear, then the next command.
