---
id: CB-12
type: task
title: "Header format: read and write"
status: todo
priority: high
owner: claude
created: 2026-11-12
parent: CB-1
blocked_by: [CB-11]
---
Read and write headers in the strict YAML subset from "Header format" in `.project/docs/file-format.md`. Writing quotes a value exactly when the rules say to. Reading rejects anything outside the subset and names the line.

Done when every header in this repo's `.project/` and every header example in the spec reads and writes back byte for byte.

## Subtasks
- [ ] Read `key: value` lines, plain values, quoted values and `[a, b]` lists
- [ ] Write values with the quoting rules
- [ ] Reject anything outside the subset, naming the line
- [ ] Round-trip tests

## Log
- 2026-11-12 21:21 claude: created
