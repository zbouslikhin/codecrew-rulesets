---
name: planning-the-detail
description: "How to plan the detailed design as small steps with milestones, before it runs on autopilot. Read at the plan stage."
---
# Planning the detail

The detailed design runs on its own, step after step, so the plan is what the person approves.

## design/plan.toml

```toml
[[step]]
title = "Slide brackets"
what = "3 per rail, two M5 T-nuts each, M4 inserts at the slide holes 165, 261, 357"
milestone = false
estimate_usd = 0.7

[[step]]
title = "The box, one piece"
what = "995 x 398 x 100, bosses for the drawer members"
milestone = true   # the person looks before it goes on
estimate_usd = 0.9
```

- One part, one joint or one assembly per step. Reference geometry first, then what attaches
  to it, then what attaches to that.
- A milestone where a mistake would be expensive to find later: the first full assembly, the
  split for the bed, anything seen from the front.
- The last step places every screw and checks everything against the agreed concept.
- Estimates: roughly $0.50 to $1.50 per step on a strong model.
