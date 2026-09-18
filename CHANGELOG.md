# Changelog

## Unreleased — v0.3

- Added task schema v2 with stable acceptance criterion IDs.
- Added criterion-linked evidence and deterministic covered/uncovered/failed reporting.
- Added latest-ledger-result semantics so a later failure invalidates an earlier pass.
- Added fail-closed handling for malformed/unknown criterion references and future task schemas.
- Preserved legacy v1 task verification without automatically rewriting existing task directories.
- Added CLI evidence recording for explicit criterion IDs.
- Added canonical project-state and anti-drift gates for long-running development.

## 0.2.0 — Beginner Preview

- Added beginner desktop GUI.
- Added guided, allowlisted Agnes/Hermes installer commands.
- Added automatic detection of Hermes managed Local Models.
- Removed Ollama as a default beginner dependency.
- Added safe Demo Project creation.
- Added Windows single-file EXE build, packaged self-test, SHA-256 output, and automatic first release.
- Upgraded GitHub Actions to Node 24-compatible v7 actions.
- Preserved strict `$0 Mode`, durable task state, and evidence gate.

## 0.1.0

- Initial CLI.
- Free Guard and Agnes/Hermes routing.
- Durable task/checkpoint/evidence state.
- Static web router demo.
