# Changelog

## 0.4.1 ? Readiness Truth & Release Surface Hardening

- Bind Agnes live-route proof to the currently present API credential and invalidate stale proof when the key disappears or changes.
- Let an already-ready Hermes Managed Local lane proceed without forcing Agnes credential entry.
- Keep Resume disabled until both a resumable task and an exact live-probe route proof exist.
- Fix empty environment mappings so isolation helpers never silently inherit process credentials or routing flags.
- Update README and public site to the released Hermes-first architecture and remove hard-coded stale release labels.

## 0.4.0 — Hermes-First Agnes API Execution

- Made Hermes Agent the primary executor; Agnes API is configured as a Hermes provider instead of requiring Agnes CLI for the beginner path.
- Added an isolated `firstwindowzero` Hermes profile with official Agnes API configuration and `fallback_providers=[]`.
- Stopped cloning the default Hermes profile; fresh setup starts without copied provider credentials.
- Added masked, explicit Agnes API key entry stored only in the isolated FirstWindow Hermes profile.
- Added live readiness proof and exact route-fingerprint gating before GUI Start/Resume.
- Added Hermes usage attestation so an unexpected provider/model or zero API calls fails closed.
- Pinned agent tool execution to the selected project with cwd, `--in`, `--no-restore-cwd`, and `TERMINAL_CWD` to protect older Hermes one-shot builds.
- Separated route execution evidence from independent task-outcome acceptance; agent exit 0 alone no longer verifies a task.
- Kept Hermes Managed Local as the verified $0 fallback and direct Agnes CLI as advanced/manual only.
- Added English / Simplified Chinese live switching, one-click readiness repair, and release-focused regression coverage.

## 0.3.0 — Verified Resume & Trusted Distribution

- Added task schema v2 with stable acceptance criterion IDs.
- Added criterion-linked evidence with deterministic covered/uncovered/failed reporting.
- Added latest-ledger-result semantics so a later failure invalidates an earlier pass.
- Added fail-closed handling for malformed/unknown criterion references and future task schemas.
- Preserved legacy v1 task verification without rewriting existing task directories.
- Added CLI evidence recording for explicit criterion IDs.
- Added Durable Resume discovery, CLI `tasks/resume`, and GUI Resume from repository checkpoints.
- Excluded verified-complete tasks from resume and treated historical evidence as untrusted data rather than executable instructions.
- Added canonical project-state and anti-drift gates for long-running development.
- Switched beginner setup to official Agnes/Hermes Desktop flows by default; remote CLI installers remain explicit advanced fallbacks.
- Made Windows Release publication version-tag driven instead of mutating an old release from main pushes.
- Added `SHA256SUMS.txt` to build artifacts and version-tag releases.
- Release publication now fails if the Git tag does not match the package version.

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
