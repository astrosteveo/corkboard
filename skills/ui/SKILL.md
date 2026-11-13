---
name: ui
description: Open this repo's Corkboard web app. Starts it in the background, or finds the one already running, and gives its URL.
disable-model-invocation: true
allowed-tools: Bash(corkboard *)
---

# Open the web app

The user ran `/corkboard:ui` to see this repo's project in the browser: the Now page, the board, the releases and each item.

1. Run `corkboard ui --background`. It starts the web app as its own process, or finds the one already running for this repo, and prints its URL and process ID. Don't run plain `corkboard ui`: it serves until it's stopped, so the command would never finish.
2. If it fails with `no .project/ folder here or above`, say this repo doesn't track its work with Corkboard yet and that `corkboard init` sets it up, then stop. For any other error, show it as it is.
3. Reply in two short lines: the URL to open, and that `kill <pid>` stops the web app. It keeps running after this session ends.
