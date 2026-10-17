---
name: cad
description: Detailed CAD stage - works through design/plan.toml step by step until the next milestone
disable-model-invocation: true
allowed-tools: Bash(bash "${CLAUDE_PLUGIN_ROOT}/bin/fc" *)
argument-hint: "[a change or note for the next steps]"
---
Stage: Detailed CAD. Work through design/plan.toml until the next milestone, then stop.

Before geometry, load freecad-pitfalls; before an assembly, placing-parts-and-screws; for printed
parts, printing-basics. Read design/decisions.md once at the start. $ARGUMENTS

For each step that isn't `done = true` in design/plan.toml:
1. Model it. Read only the files it needs. Take sizes from the standards library and
   design/results/ (measured beats assumed).
2. The edit hook checks each file you write; fix what it reports. Then render what changed
   (`bash "${CLAUDE_PLUGIN_ROOT}/bin/fc" render <file> --views iso,front`) and look. Red is an overlap.
3. A step that would change what the person agreed on in the concept: stop and ask first. A
   small decision decisions.md doesn't cover: take the obvious choice, write it into
   decisions.md marked "(assumed)", and name it in your summary.
4. Mark the step `done = true` in design/plan.toml and commit: `git add -A && git commit -m
   "<step>: <what>"`.
5. If the step is a milestone, stop the loop there.

At the milestone: run `bash "${CLAUDE_PLUGIN_ROOT}/bin/fc" check`, then ask the milestone-reviewer agent to review the
work since the last milestone (it says which files). Fix what it finds that is a real error, in
one pass. Then show the person: what was made, the checks, what the reviewer found, the
renders' file paths, the assumed decisions. Ask them to look (exports/renders/...) and say "go
on" or what to change.

When the last step is done, set cad "done" and the next stage "active" in design/flow.toml.
Between milestones the person runs /clear and /freecad-design:cad again: that's what keeps each
conversation small.
