# Web app

What each screen of the web app shows and does. `corkboard ui` serves it on localhost. It reads and writes the files described in [file-format.md](file-format.md) through the same core library as the CLI ([cli.md](cli.md)). It's plain HTML, CSS and JavaScript with no build step, and Preact, htm and marked are committed as single files, since the app works offline.

## Everywhere

- **Sidebar:** Now (with a count of items waiting on you), Board, Releases, List, Docs.
- **Ctrl-K** opens search: jump to any item or doc by ID or title, or run an action such as "New task" or "Go to v0.1". Search covers titles, descriptions and docs.
- **Keys:** `c` opens the new item form, and `Esc` closes a panel or form.
- **Live updates:** the server checks `.project/` for changed files every second and pushes the changes to the page. When Claude changes a file, the screen updates without a reload, and the item gets a dot (●) until you click Mark seen on the Now page.
- **Who:** everything you do in the app is logged as `me`.
- **Writes:** a change in the app makes the same change to the file that the matching `corkboard` command would make. Dragging a card to Done is `corkboard move <ID> done`, and so on.
- **Editing conflicts:** if Claude changes an item or doc while you're editing its text, saving shows both versions and lets you choose. Nothing is silently overwritten. Field changes such as status or priority apply to the file as it is on disk, so they never conflict.
- **GitHub:** pull requests are read with `gh` when a screen shows them, and never stored. The server reads them at most once a minute and shares them between screens, and the page asks again once a minute, since a merge changes no file in the repo. Offline or without a GitHub remote, they just aren't shown.
- **Safety:** Markdown renders with raw HTML turned off, and the server only accepts changes from the app's own page. The app can write files, so a doc in a cloned repo must never be able to run a script in it. The server listens on 127.0.0.1 only and refuses any request not addressed to `localhost:<port>` or `127.0.0.1:<port>`, so another site can't read the project by pointing its own domain name at 127.0.0.1. Its Content-Security-Policy runs only the app's own script files, never inline scripts, and no other page can frame it.
- **Theme:** light or dark, following your system setting.
- **URLs:** every screen has its own, so links can be shared between the CLI, docs and the browser:
  - `/` (Now)
  - `/board`
  - `/releases/v0.1`
  - `/list`
  - `/items/EX-12`
  - `/docs` and `/docs/architecture`

## Now

The home page: where things stand, what Claude needs from you, and what changed since you last looked.

```
v0.1 · active · due Dec 1          ███████░░░░░░░░  7/15 done

WAITING ON YOU
  EX-14  Cards flicker on drop                          bug · high
         Claude: "Should we debounce, or rebuild the column?"
         [ Reply…                                  ]  [Send]  [Mark done]

IN PROGRESS                           NEXT UP
  EX-12  Drag cards…   Claude · 1/3     EX-16  Column menu · answered
  EX-21  Write README  you              EX-13  Column limits · high
                                        EX-19  Release view

SINCE YOU LAST LOOKED  (yesterday 18:40)                   [Mark seen]
  14:20  Claude  EX-12  moved to in-progress
  14:55  Claude  EX-12  done subtask: Work out which column…
  15:02  Claude  EX-14  moved to waiting
  15:10  Claude  EX-18  created: Board column limits
```

- **Waiting on you** shows every `waiting` item with the question from its last log line.
  - **Send** moves the item to `todo` and logs your reply as `moved to todo: <reply>`, so it comes first in Claude's Next up.
  - **Mark done** is for approving a review. It moves the item to `done`, with your reply as the message if you wrote one.
- **Merged, not done** appears when an item's own pull request has merged but the item isn't `done` or `cancelled`, for example "PR #15 merged, but EX-21 Write the README is still in progress", with a **Mark EX-21 done** button. Nothing changes an item on its own.
- **In progress** and **Next up** match `corkboard now`.
- **Since you last looked** lists log lines written by Claude since you last clicked Mark seen, newest last. It only clears when you click Mark seen, not when you open the page. The time of your last Mark seen is kept in the browser, not in the repo.

## Board

Columns by status for one release.

```
Board    Release: v0.1 ▾   Epic ▾   Label ▾   Owner ▾   ☐ Group by epic   [+ New]

TODO (4)            IN PROGRESS (2)     WAITING (1)         DONE (7)
┌────────────────┐  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐
│ EX-13        ● │  │ EX-12          │  │ EX-14      bug │  │ EX-10          │
│ Board column   │  │ Drag cards     │  │ Cards flicker  │  │ Board columns  │
│ limits         │  │ between columns│  │ on drop        │  │                │
│ Board view     │  │ Board view     │  │ "debounce, or… │  │ Board view     │
│ high · ui      │  │ Claude · 1/3   │  │ high           │  │                │
│ blocked: EX-12 │  │                │  │                │  │                │
└────────────────┘  └────────────────┘  └────────────────┘  └────────────────┘
Backlog (12) and Cancelled (1) hidden · show                ● changed since you looked
```

- Shows tasks and bugs in the active release by default. Epics aren't cards; they appear as the name on each card, and as rows when **Group by epic** is on.
- A card shows its ID, title, epic, and type when it's a bug. It also shows priority when high, labels, owner, subtask progress, blockers, the question when it's waiting, and its newest own pull request with its state, such as `#14 merged`. An item's own pull requests have its ID in the title or branch name; one that only names it in the body, as pull requests often name their epic, is listed under Development but gets no badge.
- **Dragging** a card to another column changes its status. Dropping on Waiting asks for a message first.
- **Order** within a column is priority, then number, the same as `corkboard next`. Cards can't be reordered by hand.
- Backlog and Cancelled are hidden until you click **show**.
- **Clicking a card** opens it in the item side panel.

## Releases

A release and everything in it, as a tree.

```
v0.1 (active) · v0.2 (planned) · v0.0 (released) · No release

v0.1 · active · due Dec 1                  ███████░░░░░░░░  7/15 done
A board you can drag cards on, and docs pages.

▾ EX-3  Board view                 epic   in-progress   ████░░  3/6
    ✓ EX-10  Board columns                done
    ◐ EX-12  Drag cards between columns   in-progress   1/3
        ☑ Work out which column a card was dropped on
        ☐ Save the status change through corkboard
        ☐ Put the card back if saving fails
    ? EX-14  Cards flicker on drop        waiting       bug
    ○ EX-13  Board column limits          todo          blocked
▸ EX-4  Docs pages                 epic   todo          ░░░░░░  0/4
  No epic
    ○ EX-22  Fix typo in README           todo
                                                  [Copy release notes]
```

- The tabs at the top list every release, plus **No release** for items without one.
- Epics, and tasks with subtasks, expand and collapse.
- Status icons:
  - ✓ done
  - ◐ in progress
  - ? waiting
  - ○ todo or backlog
  - ✕ cancelled
- The order matches `corkboard tree`, and cancelled items stay visible.
- **Dragging** an epic onto another release's tab moves it to that release. A task with no epic can be dragged the same way.
- The goal text is the release file's body. Status and date can be changed from the header.
- **Copy release notes** copies Markdown of the release's done items, grouped by epic. Cancelled items are left out.

## List

Every item in a table, for sorting through the backlog.

```
List   Status: backlog, todo ▾   Type ▾   Label ▾   Release ▾   [+ New]

ID     Type  Status   Priority  Title                   Epic        Labels
EX-13  task  todo     high      Board column limits     Board view  ui
EX-19  task  todo     medium    Release view            Board view  ui
EX-25  bug   backlog  low       Long titles overflow    —           ui
```

- Filters work like `corkboard list`. The default shows backlog and todo.
- Clicking a column header sorts by it.
- Status and priority can be changed in the row.
- Clicking a row opens the item side panel.

## Item

One item, in a side panel over the screen you came from, or as a full page at `/items/<ID>`.

```
Board view › EX-12                                     [Full page] [×]
Drag cards between columns
In progress ▾   High ▾   Claude ▾   Release v0.1 (from epic)
Labels: ui  board  +

Description, rendered as Markdown                              [Edit]

Subtasks 1/3
  ☑ Work out which column a card was dropped on
  ☐ Save the status change through corkboard
  ☐ Put the card back if saving fails
  + Add subtask

Links
  Blocks       EX-18 Keyboard shortcuts for the board · todo
  Related to   EX-13 Board column limits · todo
  + Add link

Development
  ex-12-drag-cards
  #14 Drag cards between columns · open · checks passing
  a1b2c3d feat(board): detect drop column (EX-12) · Nov 12

Activity
  Nov 12 14:03  you     created
  Nov 12 14:20  Claude  moved to in-progress
  Nov 12 15:02  Claude  moved to waiting: should dropping on Done ask…
  [ Add a note…                                            ]

Mentioned in: Architecture (doc) · EX-14
```

- Every header field can be changed in place. Release shows "(from epic)" when it's inherited, and can't be changed there.
- Item IDs in the description show as chips, the same as in docs.
- **Edit** turns the description into a Markdown text box with a preview.
- **Subtasks** are ticked, unticked and added in place.
- **Links** shows both sides of every link, with each item's status. **+ Add link** takes a link type (blocked by, related to or duplicate of) and an item ID, or just its number, and stores the link on this item. It refuses an unknown ID, a link to the item itself, a link that's already there and a blocker that leads back to the item. An item is a duplicate of one item at most, so that type is offered only while it has none. The × on a link removes it from whichever item stores it, so removing a Blocks link changes the other item's file.
- **Development** shows the branch, pull requests and commits that mention the item's ID, as `corkboard show` lists them. Each pull request shows its state, its checks while it's open, and links to GitHub. It's hidden when there are none.
- **Activity** is the log. Notes you add go in as `me` lines.
- For an epic, the subtasks section is replaced by its tasks and bugs with their statuses and progress.
- **Mentioned in** lists docs and items that mention this ID. A doc shows its title and links to its page.

## New item form

Opened with **+ New** or `c`.

- Fields: type, title, epic, priority, owner, labels, and an optional description. Without an epic it also asks for a release, so a task made from the board lands on that board. On the board, the form starts with the release and epic it's filtered to.
- It creates the item the way `corkboard new` does, then opens it in the side panel.

## Docs

```
Search docs…          │ Architecture                                   [Edit]
▾ docs                │
    Architecture      │ The board ( EX-3 Board view · in-progress ) reads
    File format       │ items through the core library…
    CLI               │
  ▾ decisions         │ ──────────────────────────────
    0001 Markdown…    │ Mentions: EX-3, EX-12
+ New page            │ Changed Nov 12 15:40
```

- The tree on the left is the `docs/` folder: each folder's pages, then its subfolders, which collapse. A page's title is its first `#` heading, or else its file name. Typing in **Search docs** lists the pages whose title or file name has the text.
- A page's URL is its path under `docs/` without `.md`: `docs/decisions/0001-markdown.md` is `/docs/decisions/0001-markdown`. A URL ending in `.md` shows the same page, so a link to another page written for GitHub, such as `[CLI](cli.md)`, works in the app too. `/docs` shows the tree alone.
- Only `.md` files inside `docs/` are served. A path that leads out of it, through `..` or a symlink, finds no page.
- Item IDs in a page show as chips with the item's current title and status, and open the item in the side panel. IDs inside links and code, and IDs with no item, stay as text.
- **Edit** opens a Markdown text box with a preview. Saving has the same conflict check as item descriptions: if the file changed on disk since you started, both versions are shown to choose from.
- **+ New page** asks for a title and a folder, and creates `<folder>/<title-slug>.md` with the title as its `#` heading, then opens it in the editor. The folder starts as the current page's. Empty means `docs/` itself, and a name that doesn't exist yet makes the folder. In `decisions/`, the file name starts with the next number, such as `0002-`. A name that's already taken is refused.
- The footer lists the items the page mentions, when the file last changed (its modification time), and its path.
