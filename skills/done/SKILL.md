---
name: done
description: Finish the current Corkboard item - check its subtasks, run the checks, commit, and open a PR or close the item.
disable-model-invocation: true
argument-hint: "[ID]"
allowed-tools: Bash(corkboard *)
---

# Finish the current item

The user ran `/corkboard:done` to finish an item. The arguments are: `$ARGUMENTS`. An item ID there means finish that item. Nothing means finish the one you have in progress.

1. Pick the item. With an ID, use it. Without one, run `corkboard list status=in-progress owner=claude`. If there's exactly one, use it. If there's none or more than one, ask which.
2. Run `corkboard show <ID>`. If any subtask isn't ticked, list them and ask whether to finish them now or move them into a new item, then wait. A new item is made with `corkboard new task "…" parent=<the epic>`, with those subtasks piped in under `## Subtasks`.
3. Run the project's formatter, linter and tests, as its CLAUDE.md, README or config says, and fix what fails. If the project has none, say so.
4. Tick any subtask you've just finished with `corkboard sub <ID> done <N>`. If a choice made along the way is worth keeping, log it with `corkboard log <ID> "…"`.
5. Close the item, so its file goes into the same commit as the work:
   - **With a GitHub remote** (`git remote -v`): run `corkboard move <ID> waiting "PR ready for review"`. Commit what's left with the ID in the message, push the branch, and open a pull request with the ID in its title (`gh pr create`). If the user has said you merge your own PRs, merge it once its checks pass, then run `corkboard move <ID> done` on the default branch and commit that.
   - **Without one:** run `corkboard move <ID> done`, then commit what's left with the ID in the message.

   In both cases, commit the way the user's own rules say.
6. If that was the last open task or bug in its epic, move the epic to `done` too.
7. Report what you did, the PR's link if there is one, and what `corkboard next` gives.
