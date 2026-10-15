---
name: grilling-a-design
description: "How to question the person until every decision the design needs is theirs, before anything is modelled, and write them into design/decisions.md. Read before the first step of a session, and whenever a step needs a decision that isn't in decisions.md."
---
# Grilling a design

You don't design: the person does. Your job before modelling is to find every decision the
design needs, ask for it, and write down the answer. A decision you take yourself is a guess
the person finds out about later, when it costs more.

## Rounds

Ask in rounds, with ask_user. Each round holds only the questions whose answers no other open
question changes. Answers open the next round. Stop when no question is left whose
prerequisites are answered.

Work through what the design depends on, in this order:

1. **What exists.** What it fits into or onto: the frame, the space, the obstacles, what is
   already there and must not change.
2. **What it must do.** What goes in or on it, how heavy, how it moves, how often, who uses it.
3. **Bought parts.** Slides, hinges, fasteners, magnets: which ones, by model number.
4. **How it's made.** The printer and its bed, the material, other processes (cut plate,
   bought profiles).
5. **How parts join.** Screws, inserts, clips, glue; where parts split to fit the bed.
6. **Look and touch.** What's seen, what a hand meets, colours, edges.

## Each question

- **Confirm how you read the pictures first.** "I read the photo as: the side rails stick
  28 mm forward at top height, the front rails run between them. Right?" One wrong reading
  of an attachment invalidates everything after it.
- **Offer 2 or 3 options**, each with what it costs or gains (strength, print time, price,
  looks). Say which you'd recommend and why, in one line. The person picks.
- **Ask for numbers only they can get.** Put measurements on one list ("measure: the clear
  width between the front posts"), so they measure once.
- **"I don't know"** is an answer: write it down as open. Don't fill it in.
- **"You choose"** is an answer too: write your pick with its reason, marked as yours, so it
  can be changed later.

## decisions.md

Write the answers into design/decisions.md as you get them, one line per decision, grouped by
the six headings above, and the printer's bed into design/printer.toml (`bed_mm = [x, y, z]`).
Only what the person said, in plain words. At the end, give a summary of what's decided, what's
open, and the measuring list, and ask whether to start the first step.

```markdown
# Decisions

## What exists
- Frame: 3030 profiles, 1081 wide, 470 deep. Front rails run between the side rails.
- The top side rails stick 28 mm forward of the front face, at top height.

## Bought parts
- Slides: Hettich KA 5632, 400 mm, side mount. (agent's pick: the person said "you choose";
  45 kg rating, sold at Hornbach)

## Open
- Clear width between the front posts: to be measured.
```

## During modelling

When a step needs a decision decisions.md doesn't have, stop and ask that one question the
same way, with options, before you model it. Never decide it yourself and mention it after.
