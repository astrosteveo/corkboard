---
name: next
description: Start the next Corkboard item, or the one named, and begin working on it.
disable-model-invocation: true
argument-hint: "[ID]"
allowed-tools: Bash(corkboard *)
---

# Start the next item

The user ran `/corkboard:next` to start work. The arguments are: `$ARGUMENTS`. An item ID there, such as `EX-12`, means start that item. Nothing means start the next one in the order of work.

1. Check what you already have open: `corkboard list status=in-progress owner=claude`. If an item is in progress, say which one and ask whether to finish it first or park it. Wait for the answer. To park one, run `corkboard move <ID> todo "Parked to start <new ID>"`.
2. Pick the item. With an ID, run `corkboard show <ID>`. Without one, run `corkboard next`, which shows the item and says why it's next. If it prints `nothing to do`, say so and suggest `/corkboard:plan` to plan more work, then stop.
3. Run `corkboard move <ID> in-progress`. If the item's epic is still `todo`, move the epic to `in-progress` too.
4. If you're on the default branch, switch to a branch named after the item's file name, which `corkboard show` prints as `path:`. For example, `EX-12-drag-cards.md` becomes `ex-12-drag-cards`.
5. Say in a few lines what you'll do, from the item's description and subtasks, then start. While you work, follow the `corkboard:track` skill: tick subtasks as you go, log choices worth keeping, and put the ID in every commit message.
