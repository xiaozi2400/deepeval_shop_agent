---
name: review-changes
description: Review the current uncommitted changes using blast-radius and test-coverage analysis from the claude-graph knowledge graph.
---

# Review Changes

1. Run `git diff --name-only` to find the changed files.
2. Call `get_impact_radius_tool` with those file paths to find affected
   callers, importers, and tests.
3. Call `query_graph_tool` with pattern `file_summary` on each changed
   file to see what functions/classes it defines.
4. Summarize: what changed, what could break (callers/importers), and
   whether covering tests exist. Flag any changed function with no
   corresponding test file.
