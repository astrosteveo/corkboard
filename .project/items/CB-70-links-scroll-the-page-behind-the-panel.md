---
id: CB-70
type: bug
title: Links scroll the page behind the panel, and a bare % blanks the app
status: done
priority: low
owner: claude
created: 2026-11-13
parent: CB-53
labels: [ui]
---
Every in-app link scrolls to the top, including links that only open the item panel, so the page behind it loses its place. And a URL with a bare `%`, such as `/docs/50%`, throws `URIError` in the router and shows a blank page instead of Not found.

## Subtasks
- [x] Opening the panel keeps the page's scroll
- [x] A path that won't decode shows Not found
- [x] Checked in a browser

## Log
- 2026-11-13 20:04 claude: created
- 2026-11-13 20:33 claude: moved to in-progress
- 2026-11-13 20:34 claude: done subtask: Opening the panel keeps the page's scroll
- 2026-11-13 20:34 claude: done subtask: A path that won't decode shows Not found
- 2026-11-13 20:34 claude: done subtask: Checked in a browser
- 2026-11-13 20:34 claude: moved to done
