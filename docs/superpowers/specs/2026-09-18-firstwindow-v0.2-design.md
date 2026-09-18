# FirstWindow v0.2 Beginner Design

## Goal

Close the gap between the product promise (“your first coding agent”) and the v0.1 CLI engine.

## Canonical user flow

```text
Download
→ Open FirstWindow
→ Diagnose
→ Set Up $0 Path
→ Choose Folder
→ Describe Task
→ Start
→ Agent runs
→ checkpoint + evidence
```

## Runtime policy

Automatic `$0 Mode`:
1. Agnes only when the user explicitly confirms the configured provider is free.
2. Hermes when its non-secret model config reports a managed `llamacpp` local model.
3. Otherwise block.

No silent cloud fallback.

## Setup policy

FirstWindow may offer documented official Agnes/Hermes installer commands, but:
- commands are fixed/allowlisted in source
- the exact command is shown
- execution requires user confirmation
- credentials are never captured
- Hermes model selection remains in Hermes Desktop because hardware/download requirements vary

## Distribution

Windows is the first packaged target:
- PyInstaller one-file/windowed
- packaged `--self-test`
- artifact upload
- SHA-256 build log
- first successful main build creates v0.2.0 release

## Non-goals

- no new LLM runtime
- no billing-provider guessing
- no silent authentication
- no code signing in v0.2
- no unattended destructive permissions
