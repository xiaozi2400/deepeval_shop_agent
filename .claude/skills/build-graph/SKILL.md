---
name: build-graph
description: Build or update the claude-graph knowledge graph for this repository.
---

# Build Graph

1. Call `get_graph_stats` to check whether a graph already exists.
2. If it does not exist, call `build_or_update_graph` to run a full build.
3. If it exists, call `build_or_update_graph` to run an incremental update.
4. Report the resulting node/edge/file counts.
