# freecad-design: FreeCAD parts with Claude Code

Design parts in FreeCAD 1.1 with Claude Code, on your Claude subscription: you decide, Claude
models, checks, renders and shows. The same design flow as codecrew's freecad-model ruleset,
as a Claude Code plugin.

## What you get

- **Stage commands**, in order: `/freecad-design:start`, `grill`, `concept`, `risks`, `pieces`,
  `plan`, `cad`, `analyse`, `prototype`, `inspect`, `test`, `release`, and `status` for where
  the design is (kept in `design/flow.toml`).
- **Checks by themselves:** after each file Claude writes, that part or assembly is checked
  (builds into a valid solid, fits your bed, nothing overlaps, enough thread); before Claude
  finishes a turn, everything is, when anything changed. Errors go straight back to Claude.
- **A reviewer at milestones:** `/freecad-design:cad` works through `design/plan.toml` and
  stops at each milestone, where a reviewer agent (on Sonnet, with fresh eyes) checks the work
  before you look.
- **Tools** (`bin/fc`, run with FreeCAD's own Python): `check`, `render`, `export` (STLs
  turned onto the face they print on), `analysis`, `status`, `setup`, `new`.

## Install (Windows)

1. **FreeCAD 1.1** from https://www.freecad.org/downloads.php (the installer, default folder).
2. **Git for Windows** from https://git-scm.com/downloads/win (Claude Code runs the tools in
   its Git Bash).
3. **Claude Code in VS Code:** install the "Claude Code" extension, open it, sign in with your
   Claude account. Make sure no `ANTHROPIC_API_KEY` environment variable is set, or it bills
   the API instead of your subscription.
4. **The plugin**, in a Claude Code chat:
   ```
   /plugin marketplace add zbouslikhin/codecrew-rulesets
   /plugin install freecad-design@zb-design
   ```
5. Open your design folder in VS Code, start a Claude Code chat there and run
   `/freecad-design:start`. It finds FreeCAD, adds what's missing (Pillow, ruff, pytest) when
   you agree, and adopts the project, or sets up a new one.

FreeCAD somewhere unusual: set the environment variable `FREECAD_PYTHON` to its python, e.g.
`C:/Program Files/FreeCAD 1.1/bin/python.exe`.

## Working with it

- **One stage per conversation:** each stage ends by telling you to run `/clear` and the next
  command. The design lives in the files (`design/decisions.md`, the TOMLs, git), not in the
  chat, so a fresh conversation loses nothing and stays small.
- **CAD runs milestone to milestone:** `/freecad-design:cad`, look at what it shows you
  (`exports/renders/...`, or the STEP in FreeCAD), then `/clear` and `/freecad-design:cad`
  again, with a note if you want a change (`/freecad-design:cad make the lip 2 mm deeper`).
- **Undo:** Claude Code's rewind (Esc twice), or git: each CAD step is a commit.
- **The full check** runs before Claude finishes a turn in which anything was modelled: about a
  minute for a large assembly. When nothing changed since it passed, it takes no time.
