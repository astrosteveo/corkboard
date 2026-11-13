---
id: CB-27
type: task
title: The page shell
status: done
priority: high
owner: claude
created: 2026-11-12
parent: CB-4
blocked_by: [CB-24]
---
`corkboard/web/index.html` and the app's JavaScript, with Preact, htm and marked committed as single files, so the app works offline with no build step. Routes for `/`, `/board`, `/releases/<name>` and `/items/<ID>`, a sidebar with Now, Board and Releases, light and dark themes in the mockup's look, and Markdown rendered with raw HTML turned off.

Done when the page loads with the network off, every route renders, and a `<script>` in an item's description shows as text.

## Subtasks
- [x] Commit Preact, htm and marked, with their licenses
- [x] index.html, the routes and the sidebar
- [x] Light and dark themes from the mockup
- [x] Markdown with raw HTML turned off
- [x] Check it in a browser

## Log
- 2026-11-12 22:45 claude: created
- 2026-11-12 23:32 claude: moved to in-progress
- 2026-11-12 23:38 claude: done subtask: Commit Preact, htm and marked, with their licenses
- 2026-11-12 23:38 claude: done subtask: index.html, the routes and the sidebar
- 2026-11-12 23:38 claude: done subtask: Light and dark themes from the mockup
- 2026-11-12 23:38 claude: done subtask: Markdown with raw HTML turned off
- 2026-11-12 23:38 claude: done subtask: Check it in a browser
- 2026-11-12 23:38 claude: Vendored Preact 10.29.8 (not 11, which is weeks old), htm 3.1.1 and marked 18.1.2 from their npm tarballs, checked against the registry's sha512. hooks imports ./preact.module.js instead of 'preact', so no import map is needed and the CSP can forbid inline scripts. Versions and changes are in corkboard/web/vendor/README.md.
- 2026-11-12 23:38 claude: Markdown: marked's html renderer escapes raw HTML, then links and images keep only http, https, mailto or same-site URLs, judged by the browser's URL parser. Every response carries a CSP with script-src 'self'. Checked in headless Chromium (Playwright) on a demo repo: <script>, onerror and javascript: links all show as text, no request leaves localhost, and every route renders in light and dark.
- 2026-11-12 23:38 claude: moved to done
