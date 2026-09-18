# FirstWindow v0.2 Beginner Implementation Plan

> **For agentic workers:** execute changes with evidence gates; do not merge before Linux CI, Windows packaging, and PR checks pass.

**Goal:** Make FirstWindow usable as a beginner-facing Windows preview without weakening the v0.1 free-cost and durable-state guarantees.

**Architecture:** Keep the tested Python core provider-neutral. Add a thin Tkinter GUI over setup, routing, durable task state, and agent adapters. Use Hermes managed Local Models as the default local path.

**Tech Stack:** Python 3.10+ stdlib, Tkinter, PyInstaller only at build time, GitHub Actions, static web demo.

**Spec:** `docs/superpowers/specs/2026-09-18-firstwindow-v0.2-design.md`

## Tasks

- [x] RED: define setup, onboarding, demo, managed-local behavior with failing tests.
- [x] GREEN: implement beginner setup and managed-local detection.
- [x] RED: prove provider override/local-status gaps.
- [x] Implement provider-safe Hermes invocation and safe status probe.
- [x] Build beginner GUI over tested core.
- [x] Add Windows one-file packaging + packaged self-test.
- [x] Add beginner docs and update CI actions.
- [ ] Linux CI passes on final branch head.
- [ ] Windows App workflow passes on PR.
- [ ] PR acceptance/review passes.
- [ ] Merge to main.
- [ ] Main Windows build publishes v0.2.0 binary.
- [ ] Redeploy/verify public website.
