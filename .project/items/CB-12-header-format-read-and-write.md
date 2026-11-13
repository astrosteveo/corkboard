---
id: CB-12
type: task
title: "Header format: read and write"
status: done
priority: high
owner: claude
created: 2026-11-12
parent: CB-1
blocked_by: [CB-11]
---
Read and write headers in the strict YAML subset from "Header format" in `.project/docs/file-format.md`. Writing quotes a value exactly when the rules say to. Reading rejects anything outside the subset and names the line.

Done when every header in this repo's `.project/` and every header example in the spec reads and writes back byte for byte.

## Subtasks
- [x] Read `key: value` lines, plain values, quoted values and `[a, b]` lists
- [x] Write values with the quoting rules
- [x] Reject anything outside the subset, naming the line
- [x] Round-trip tests

## Log
- 2026-11-12 21:21 claude: created
- 2026-11-12 21:31 claude: moved to in-progress
- 2026-11-12 21:37 claude: done subtask: Read `key: value` lines, plain values, quoted values and `[a, b]` lists
- 2026-11-12 21:37 claude: done subtask: Write values with the quoting rules
- 2026-11-12 21:37 claude: done subtask: Reject anything outside the subset, naming the line
- 2026-11-12 21:37 claude: done subtask: Round-trip tests
- 2026-11-12 21:37 claude: Fuzzed the reader and writer against PyYAML (run through uv, not a dependency), 300,000 random values each way. Found that YAML parsers reject many characters inside [ ], so unquoted list items now use an allowlist (letters, digits, spaces, . / - _), and that a bare = or << is a special key. After the fixes: zero disagreements either way. The spec's quoting rule now matches the code exactly.
- 2026-11-12 21:37 claude: moved to done
