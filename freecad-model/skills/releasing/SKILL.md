---
name: releasing
description: "How to end a design: decide with the person what to do about a failed test, then the print pack with what to print, buy and assemble and what was proved. Read at the release stage."
---
# Releasing

## A failed test first

If design/results/testing.json has a failure, ask with ask_user before anything else:

- a revision: what you'd change and which stages run again (usually the detailed design, then
  only the failed test). The person starts it from the dashboard ("Make a revision").
- release as it is: the known issue goes into the pack, with what to watch for.

## The pack: design/release.toml

Export (`python -B scripts/export.py`) and write:

```toml
revision = "B"

[[print]]
part = "tray_tile"
count = 10
file = "exports/tray_tile.stl"
prints_on = "its floor"

[[buy]]
item = "Hettich KA 5632/400, 1 pair"
where = "Praxis"
price = "€24.99"

[[assemble]]
text = "Melt the inserts into the brackets and tiles."

[[proved]]
what = "Front drop at full extension"
by = "test 1, rev A: 3.4 mm"

[[not_proved]]
what = "Brackets walking along the rail"
why = "testing was skipped"
```

Every stage that was unticked or skipped goes under not_proved with what it would have
checked. Prices you don't know stay out: never invent one.
