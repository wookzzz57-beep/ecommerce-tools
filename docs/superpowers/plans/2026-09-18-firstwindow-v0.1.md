# FirstWindow v0.1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans task-by-task.

**Goal:** Ship a testable free-first Coding Agent launcher with Agnes/Hermes adapters, durable state and public demo.

**Architecture:** Separate cost policy, routing, external adapters and durable state. Fail closed in $0 Mode.

**Tech Stack:** Python 3.10+ stdlib, static HTML/CSS/JS, GitHub Actions, Vercel.

**Spec:** `docs/superpowers/specs/2026-09-18-firstwindow-v0.1-design.md`

## Tasks
- [x] Free Guard and router with tests.
- [x] Durable task/checkpoint/evidence core with tests.
- [x] Agnes and Hermes adapters with tests.
- [x] CLI doctor/route/run/verify.
- [x] Responsive public router demo.
- [x] GitHub Actions workflow.
- [ ] Verify CI on feature branch.
- [ ] Deploy and verify Vercel URL.
