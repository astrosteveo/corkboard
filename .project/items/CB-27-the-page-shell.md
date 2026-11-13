---
id: CB-27
type: task
title: The page shell
status: todo
priority: high
owner: claude
created: 2026-11-12
parent: CB-4
blocked_by: [CB-24]
---
`web/index.html` and the app's JavaScript, with Preact, htm and marked committed as single files, so the app works offline with no build step. Routes for `/`, `/board`, `/releases/<name>` and `/items/<ID>`, a sidebar with Now, Board and Releases, light and dark themes in the mockup's look, and Markdown rendered with raw HTML turned off.

Done when the page loads with the network off, every route renders, and a `<script>` in an item's description shows as text.

## Subtasks
- [ ] Commit Preact, htm and marked, with their licenses
- [ ] index.html, the routes and the sidebar
- [ ] Light and dark themes from the mockup
- [ ] Markdown with raw HTML turned off
- [ ] Check it in a browser

## Log
- 2026-11-12 22:45 claude: created
