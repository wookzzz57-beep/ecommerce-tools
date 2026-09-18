# FirstWindow Beginner Guide

FirstWindow is built around one rule:

> **$0 Mode never silently falls back to a provider whose cost is unknown.**

## Windows — shortest path

1. Download `FirstWindow-Windows-x64.exe` from GitHub Releases.
2. Open it and press **Diagnose**.
3. Press **Set Up $0 Path**.
4. If Hermes is missing, FirstWindow offers the documented official Hermes installer and shows the exact command before running it.
5. Hermes Desktop opens for the one-time **Local Models** step:
   - Settings → Providers → Local Models
   - Install runtime
   - Download a model appropriate for your machine
   - Click **Use**
6. Return to FirstWindow and press **Diagnose**.
7. Choose a project folder, describe the task, and press **Start Building**.

Hermes manages its own local llama.cpp runtime and model files. After a model is downloaded, that lane can run locally without an API key.

## Optional Agnes fast lane

Agnes Code is the second runtime. Install it from FirstWindow or with its official installer, sign in once, then configure a provider that is free for your account.

Because Agnes supports both free and paid providers, FirstWindow does **not** guess. Check **I confirmed my Agnes provider is free** only after you have verified that fact.

Automatic mode routes:

1. Agnes Free, when explicitly confirmed.
2. Hermes Local, when a managed local model is detected.
3. Otherwise: stop. No paid fallback.

## Demo Project

Press **Create Demo** in the GUI, or run:

```bash
firstwindow demo
```

This creates a tiny dependency-free HTML project with a suggested first task.

## What FirstWindow automates

- runtime detection
- allowlisted official installer selection
- $0 routing policy
- task creation
- checkpoint persistence
- agent launch
- exit evidence
- safe demo creation

## What remains intentionally interactive

Two setup steps are not silently automated:

- Agnes account/provider authentication
- Hermes local-model selection/download, because machine memory and download size vary

FirstWindow guides those official flows instead of storing credentials or silently choosing a large model.

## Windows warning

The v0.2 community binary is not code-signed yet. Windows SmartScreen may show an unknown-publisher warning. The GitHub Actions build runs a packaged self-test and prints a SHA-256 hash in its log.
