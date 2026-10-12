# freecad-part

## v2.10.0

Onshape moves out of codecrew into this ruleset (codecrew's ruleset hooks). The Onshape builder's hand-over and the `sync` pipeline work from these records as before.

- **`project_settings`: the Onshape Part Studio** (its URL; context `onshape`, shared with the
  other rulesets that work in Onshape). Asked for on the Projects page; the designer's task names
  it. Projects that had an Onshape document keep it: codecrew moves it into this setting.
- **`guards`: the Onshape design guard**, offered on an agent's page for its Onshape server: only
  Part Studio feature work, only in the project's Part Studio and branch, nothing that writes
  outside code-writing stages, no `file_refs`.
- **`recorders`: `features`** (the feature list, without the fields that change with every
  request, into `design/onshape/features.json`) and **`properties`** (volume, mass and bounding
  box in mm³, g and mm, into `design/onshape/properties.json`, by `properties.py`). Proven by
  `fixtures/recorders/`.
- Needs a codecrew with ruleset hooks: from it on, codecrew records nothing from Onshape for a
  project whose ruleset is older than this version. Older codecrews ignore the sections.

## v2.9.0

Strength by hand calculation (block F of the mechanical-design roadmap).

- **A spec states what the part must carry.** `[[loads]]`, each with a model (`cantilever`,
  `simply_supported`, `tension`, `screws_in_shear`, `snap_arm`), a force, and dimensions that
  are parameters of `Params`; `safety_factor` for the spec or per load. Optional:
  `max_deflection_mm`, `stress_concentration`, `repeated` for a snap arm.
- **The `validate` check calculates each load** on the built part's parameters and holds it to
  its safety factor: `overstressed`, `too-flexible`, `overstrained`, `screw-overloaded`. A load
  that is carried is reported with its numbers.
- **`check:strength`** proves a requirement; the report gets a Strength section with every
  calculation.
- **`standards/strength.py`**: sections (rectangle, round, tube), the beam cases, screws in
  shear (stress area from the thread, yield by property class), snap-arm strain and force,
  permissible strains for the plastics.
- **`strength_factor` per process** (`processes.toml`): how much of the material's datasheet
  strength a part made that way keeps. 0.5 for FDM, 0.8 for SLA and SLS, 1.0 otherwise;
  a project sets its own in `design/processes.toml`.
- The spec check: `unknown-load-model`, a load's dimension typed as a number, an unknown
  parameter, loads without a safety factor, `check:strength` without loads.
- New fixture part `snap_latch`; `mounting_bracket` carries two loads. Skill `checking-strength`.
- Limits: straight members of constant section under a static load. No finite-element
  analysis, fatigue, creep, impact or buckling; stress around details only through a factor
  you give. The loads are not re-checked across the 10% variation of the parameters. The
  permissible strains and the strength factors are typical design-guide figures, not
  measurements: set your own.


## v2.8.0

Hand-over to Onshape (block J of the mechanical-design roadmap).

- **A part proven here can be rebuilt in Onshape and kept the same.** `design/handover.toml`
  names the part that goes to the project's Part Studio. An *Onshape builder* agent recreates
  it there: one variable per dimension of `Params` (the same name without its unit, a plain
  value), then the features in `build()` order.
- **The `handover` check** compares codecrew's record of the Part Studio with the part here:
  every variable present with the same value (`variable-missing`, `variable-differs`,
  `variable-not-literal`), the same volume to 0.1% and the same size to 0.01 mm
  (`volume-differs`, `size-differs`), and Onshape's measurements recorded at all
  (`handover-unverified`).
- **Accepting** a hand-over records the Onshape features (`design/onshape/handover.lock.json`).
  From then on a feature added, removed, reordered or re-dimensioned in Onshape is `drift`.
- **Variable values changed in Onshape are taken back** into the part's `Params` before the
  checks run (`handover-pull`), so every check judges the changed part: a change that breaks a
  wall, an envelope or a fit is reported to whoever made it.
- Pipeline templates *Hand a part over to Onshape* (rebuild, then accept) and *Take changes from
  Onshape* (pull, then every check; a failure goes to you, nobody fixes it away).
- Skill `handing-over-to-onshape`.
- Needs a codecrew that records Onshape's measurements (`design/onshape/properties.json`).
- Limits: one part per project's Part Studio; equivalence is variables, volume and bounding
  box, not a comparison of the surfaces; nothing here was run against a live Onshape.


## v2.7.0

The engineer's workflow (block I of the mechanical-design roadmap).

- **A pipeline template, `design`:** requirements (a gate: you approve the specs before
  anything is modelled), concept (a thinking stage, saved as `design/<branch>.concept.md`),
  design, and a design review. codecrew offers it per project on the Pipelines page and creates
  it with a new project.
- **Proposed specs.** A spec may say `status = "proposed"`: written and approved before its part
  exists. What it names (the part, its parameters, its tests) needn't exist yet; it shows as a
  warning (`spec-proposed`). Once the part is built the status must go
  (`spec-still-proposed`), and the spec is checked against the part in full.
- **Agent templates:** a new *requirements engineer* (writes specs only, in `design/` and
  `reference/`); the engineer and the reviewer now start from the skills below.
- Skills `engineering-workflow` (the order of work, and which skill to read when) and
  `design-review` (what the checks already guarantee, and the nine things only a reviewer can
  judge).
- Needs a codecrew that knows pipeline templates in a ruleset; older versions ignore them.


## v2.6.0

Industrial design (block H of the mechanical-design roadmap).

- **A spec says whether people meet the part:** `[appearance]` with `visible` and `touched`.
  Without it, a warning (`appearance-unstated`): the rules below can't be applied.
- **Touched parts have no sharp outer edges** (`sharp-edge`): an outside edge whose faces turn
  by 60 degrees or more must be broken by a radius or chamfer. The face the part `rests_on` is
  exempt.
- **Visible parts** state a `colour` and a `finish` (`spec-incomplete`), the finish must suit
  the material and process (`finish-material`; `standards.finishes`), and the part keeps to
  three different radii or fewer (`radius-family`).
- **What a hand holds** is declared in `[[grips]]` and must be a size hands need (`grip-size`):
  handle diameter and length, pinch grip, finger hole, hand opening, push button. The ranges
  are in `ergonomics.toml`; a project overrides them in `design/ergonomics.toml`.
- **Shaded views** are generated for every part, `deliverables/<part>/views.svg`: two fixed
  corners, the same for every part, shown at the top of its report.
- Skill `designing-for-people`, with the reviewer's checklist for what can't be measured.
- The ergonomic ranges are guideline values for adult hands without gloves. Check them against
  your users and the standard you design to.


## v2.5.0

Deliverables (block G of the mechanical-design roadmap).

- **`deliverables/` is generated** from the specs and the built geometry, before the checks
  run, and committed with the work:
  - per part, `drawing.svg`: front, top, right and isometric views with hidden lines on an A4
    sheet; a table of the critical dimensions with tolerance and limits; material, process,
    general tolerance, mass, envelope and scale in the title block;
  - per part, `report.md`: every requirement with its evidence (the test, the parameter with
    its limits, the measured envelope and mass), interfaces, critical dimensions,
    manufacturability per process, and cost;
  - per assembly, `bom.csv` and `report.md`: parts, standard and reference parts with
    quantity, material, process and mass; every joint's fit and every stack in the worst case.
  A deliverable is rebuilt only when what it's made from changed.
- **Cost** is estimated only from the project's own rates in `design/costs.toml` (material per
  kg; per process an hourly rate, a volume rate, setup, tooling, stock and waste). Without
  rates the report says so. No prices ship with the ruleset.
- **Critical dimensions** are the parameters an interface names, those in `[[standards]]` and
  `[[tolerances]]`, and those that prove a requirement. One without a tolerance fails
  (`dimension-untoleranced`).
- Skill `deliverables`.
- Needs a codecrew that knows `generated` in a ruleset: the files are then not counted as the
  agent's own changes (older versions still work, but an agent in plan mode would have to
  declare them).
- Limits: the drawing shows dimensions in a table, not as dimension lines on the views; the
  four views are fixed (no sections or details); the cost model is volumes times rates.


## v2.4.0

Tolerances and fits (block D of the mechanical-design roadmap).

- **What mates is toleranced.** A spec's `general_tolerance` (ISO 2768-1: f, m, c, v) covers
  every dimension; `[[tolerances]]` gives a parameter its own: an ISO 286 class (`fit = "H7"`),
  deviations (`upper_mm`, `lower_mm`) or a general class. A clearance hole declared to ISO 273
  has its class. Every parameter an interface names must be covered (`interface-tolerance`);
  a class outside the table fails (`unknown-fit`).
- **The process must be able to hold it.** Each process profile states the finest grade it
  holds (`best_tolerance_grade`: turning IT6, milling IT7, moulding IT10, laser and resin IT11,
  sheet metal and powder IT12, filament IT13). A finer tolerance fails (`tolerance-too-tight`)
  unless the spec names the operation that achieves it (`achieved_by`).
- **Across parts, in the worst case.** A joint may state its `fit` (hole, shaft, kind, and
  limits on the clearance): the least and most clearance are worked out from both parts'
  tolerances (`fit`). `[[stacks]]` in an assembly's spec are chains of signed dimensions with
  limits on their sum, added at their worst (`stack-up`). A dimension in either that has no
  tolerance fails (`untoleranced`).
- `standards.tolerances`: IT grades 5 to 14, holes H, G, F, E, D, JS, shafts d to h, js, k, m,
  n, p, sizes up to 500 mm; ISO 2768-1 general tolerances.
- Skill `choosing-a-fit`.
- Existing specs: give each a `general_tolerance`, or its interfaces fail. The `part` generator
  writes one.
- Not covered: tolerance classes outside the table (r, s, K, M, N, P holes), geometric
  tolerances (flatness, position), statistical stack-up. Stacks are worst-case sums.


## v2.3.0

Design for manufacturing (block C of the mechanical-design roadmap).

- **A part must be makeable by every process its spec names.** The built solid is measured, and
  a process profile judges it. Measured: wall thickness (thin and thick), holes (diameter,
  depth, blind or through), internal corners (sharp, or their radius and depth), overhangs,
  bridges and horizontal holes against a build direction, draft and undercuts against a
  direction of pull, the reach of the tool, closed cavities, rotational symmetry, flat-sheet
  form, bend radii, and overall size.
- **Processes are data:** `processes.toml` ships profiles for `fdm`, `sla`, `sls`, `milling`,
  `turning`, `sheet_metal`, `laser_cutting` and `injection_moulding`. A project changes limits
  for its machines, or defines processes of its own, in `design/processes.toml`, with the same
  keys.
- New findings from `validate`: `thin-wall`, `thick-wall`, `small-hole`, `deep-hole`,
  `overhang`, `sharp-internal-corner`, `tight-internal-corner`, `deep-corner`, `unreachable`,
  `no-draft`, `undercut`, `enclosed-void`, `not-rotational`, `too-slender`, `not-flat-sheet`,
  `tight-bend`, `too-large`. Each says the process, where on the part, and how much.
- The spec may state `[orientation] up`: how the part lies in the machine (default "+z").
- Skill `designing-for-a-process`.
- Proven on real geometry: a good part for each kind of process that must pass (printed,
  milled, laser-cut, turned, moulded), and a case per finding.
- Limits: the profiles are the usual design-guide values, not your shop's. Not checked: the
  distance of holes from bends and whether sheet metal unfolds; milling reach is judged along
  the up axis only unless the project adds directions; a part made by two operations in
  sequence (turned, then milled) can't be expressed yet.


## v2.2.0

Standards (block B of the mechanical-design roadmap), and with them fastener checks in
assemblies (the rest of block E).

- **A standards library ships with the ruleset**, as the read-only package `standards/` in the
  project: `fasteners` (metric threads, ISO 273 clearance holes, ISO 2306 tap drills, ISO 4762
  socket head screws, DIN 974-1 counterbores, ISO 4032 nuts, ISO 7089 washers, screw lengths),
  `sizes` (stocked sheet thicknesses, DIN 250 radii, drill steps, ISO 3 preferred numbers),
  `materials` (17 plastics and metals with density, typical strength and the processes that
  suit them) and `shapes` (screws as geometry). Parts take their numbers from it.
- **Spec:** `[[standards]]` says which parameter follows which standard. The material must be
  in the library (`unknown-material`) and made by a process that suits it (`unknown-process`,
  `material-process`). An interface that mates with a thread needs a parameter held to a
  standard for that thread (`interface-standard`). A standard part's designation must be one
  that exists (`standard-part`; unknown standards are a warning).
- **Measured on the built part:** a declared parameter has a value its standard allows, or a
  stated reason (`nonstandard-size`). The mass comes from the material's density; a part's own
  `DENSITY_G_CM3` must agree with it (`density-mismatch`).
- **Assemblies:** the screws the spec lists are placed (`component-missing`). A screw in a
  tapped hole (modelled at its tap-drill diameter) counts as thread engagement, not
  interference; it must engage enough thread for the material it's in (`thread-engagement`),
  and there must be room above its head for the tool (`no-tool-access`).
- Skills `choosing-a-fastener` and `standard-sizes`.
- Proven by 56 fixture cases on real geometry (9 new here).
- The tables hold common metric sizes; check a value against your own copy of the standard
  before manufacture. The strength figures are typical values for comparison only.


## v2.1.0

Assemblies (block E of the mechanical-design roadmap).

- **An assembly is a module**, `assemblies/<name>.py`: `build()` returns its placed components
  as a dict, name -> `Part.Shape`. Reference CAD the design must fit lives in `reference/` as
  STEP files and is placed like any other component.
- **Checked by `validate`, against the assembly's spec:** every part is placed as often as the
  spec says (`component-missing`, `component-unknown`); no two components occupy the same space
  (`interference`, with how much and where); the two sides of a fixed joint meet (`joint-open`);
  a sliding or rotating joint keeps its `clearance_mm` (`clearance`); `assembly-contract`; a
  test per assembly (`missing-test`).
- **Spec:** an assembly spec needs its module (`spec-orphan`); a joint has a `kind` (fixed,
  sliding, rotating), and a moving joint must state its `clearance_mm`.
- The template has an example: the bracket on a frame rail, placed from the rail's own
  geometry. Skill `placing-an-assembly`. The engineer template may write `assemblies/**` and
  `reference/**`.
- Proven by 9 new fixture cases, on real geometry.
- Not yet: standard parts (screws) as geometry, and whether a fastener can be reached. Both
  need the standards library (block B).


## v2.0.0

Requirements as data (block A of the mechanical-design roadmap). A major version: a part
without a spec now fails.

- **Every part starts from a spec**, `design/<part>.spec.toml`: purpose, quantity, material,
  processes, the envelope and mass it must stay within, what the design starts from (text, a
  drawing, CAD it must fit), its interfaces with the parameters that realise them, and its
  requirements, each with what proves it. Assemblies have a spec too: their parts (this
  repository's, standard parts, reference CAD) and the joints between their interfaces.
- **New check `spec`** (reads files only): the spec is complete and names what exists
  (`spec-incomplete`, `spec-invalid`, `spec-name`, `spec-orphan`, `no-spec`, `duplicate-id`,
  `source-missing`, `unknown-part`, `unknown-interface`), every interface is realised by a
  parameter (`interface-unrealised`, `unknown-parameter`), and every requirement is proven by a
  test, a parameter or a measured target (`requirement-unproven`, `unknown-test`,
  `unknown-proof`).
- **The targets are measured** on the built part by `validate`: `over-envelope` (in any
  orientation), `over-mass`, and `mass-unknown` when the spec sets a mass but the part has no
  density.
- **Existing projects:** run `python .codecrew/rulesets/freecad-part/check_spec.py --grandfather`
  once. It lists today's parts without a spec in `design/legacy.toml`; for those a missing spec
  is a warning. New parts need one.
- The `part` generator also writes the spec's skeleton. The engineer template may write
  `design/**`. Skill `writing-a-spec`.
- Plan mode: interfaces, process limits and targets are no longer retyped in the plan (they are
  in the spec); a planned new part must plan its spec (`part-has-spec`).
- Proven by 17 new fixture cases. Needs Python 3.11 (`tomllib`), which the toolchain image has.


## v1.4.0

- Skills (agents see the list, and load one with `read_skill` when the task touches it):
  `edges-by-geometry` (selecting edges and faces so fillets survive parameter changes) and
  `import-order` (FreeCAD before Part, and the layout of a part module). Needs a codecrew with skills; older versions don't install the folder.

## v1.3.0

- Permission rules. Denied: `git push`, `git commit`. Needs you (refused for now):
  `pip install` (parts are checked in the toolchain image, not in what an agent installs).
  Allowed, also for agents that only run allowed commands: `python`, read-only git.
- Proven by `fixtures/permissions.yaml`. Needs a codecrew with permission rules; older versions ignore the section.

## v1.2.0

- Plan mode: a plan has a parameter table, interfaces and mating dimensions, process limits,
  targets for size and mass, and its files. Plan checks: every parameter has a unit and a
  rationale and its unit in its name, every new part has a planned test, new files fit the
  structure rules.
- The engineer template starts with plan mode *ask on risk*.
- Proven by `fixtures/plans/`. Needs a codecrew with plan mode; older versions ignore the section.

## v1.1.0

- Generator `part`: the scaffold tool (or `make scaffold`) writes parts/<name>.py and
  tests/test_<name>.py, a skeleton that passes every check; the engineer template has the tool.

## v1.0.1

- Python outside parts/, tests/ and scripts/ is an error (outside-parts), with where it
  belongs: a part in src/parts/ used to pass unchecked.

## v1.0.0

Parametric parts scripted with FreeCAD 1.1 (headless). Engineering checks (contract, units in
parameter names, valid solid, parametric robustness at +/-10%, STEP export, a test per part),
ruff, pytest. Project template (an L-shaped mounting bracket), agent templates (engineer,
reviewer, researcher), toolchain Dockerfile.
