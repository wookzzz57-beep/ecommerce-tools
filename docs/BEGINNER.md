# FirstWindow Beginner Guide

FirstWindow follows one hard rule:

> **$0 Mode never silently falls back to a provider whose cost is unknown.**

It also has one execution rule:

> **Hermes Agent is the primary executor. Agnes API is configured as a Hermes provider. Agnes CLI is optional/advanced only.**

## Windows — shortest path

1. Download `FirstWindow-Windows-x64.exe` and `SHA256SUMS.txt` from the same GitHub Release.
2. Optionally verify the download:

```powershell
Get-FileHash .\FirstWindow-Windows-x64.exe -Algorithm SHA256
Get-Content .\SHA256SUMS.txt
```

The two SHA-256 values must match.

3. Open FirstWindow and choose **English** or **简体中文**.
4. Press **Make Me Ready / 一键就绪**.
5. If Hermes is missing, FirstWindow asks once before running the official installer.
6. FirstWindow creates or repairs its isolated Hermes profile: `firstwindowzero`.
7. The profile is created blank. FirstWindow does **not** clone your default Hermes profile or copy its provider credentials.
8. If `AGNES_API_KEY` is missing from the isolated profile, FirstWindow opens a masked input dialog. Paste the Agnes API key you want this profile to use.
9. Confirm that the current Agnes API account/key route is free for your account. FirstWindow does not guess billing status.
10. FirstWindow binds that confirmation to the current key for this app session. If the key is removed or changed, the old route proof is invalidated and the cloud lane must be reconfirmed/re-probed.
11. FirstWindow disables fallback providers and runs a real Agnes-through-Hermes readiness probe.
12. The probe must return `FIRSTWINDOW_READY`, and Hermes usage evidence must show the expected Agnes model/provider and at least one API call.
13. Only then can Start/Resume execute on that exact route. If Hermes Managed Local is already ready, FirstWindow can verify/use it without requiring an Agnes key.
14. Choose a project folder, describe the task, and press **Start Building**.

If the Agnes cloud lane cannot be verified, FirstWindow can use **Hermes Managed Local** when a validated local model is ready. If neither verified $0 route exists, FirstWindow blocks instead of switching to a paid provider.

## What “Agnes API via Hermes” means

```text
FirstWindow
  └─ Hermes Agent
       ├─ Agnes API         ← primary cloud lane
       └─ Managed Local     ← local fallback
```

FirstWindow does not need Agnes CLI to run the primary cloud lane.

The direct Agnes CLI installer remains available only under the advanced/manual setup surface for users who intentionally want it.
## Credential boundary

The Agnes key entered in FirstWindow is written only to the isolated `firstwindowzero` Hermes profile.

FirstWindow does not:

- copy the default Hermes `.env`
- import OpenAI/DeepSeek/OpenRouter keys
- print the Agnes key to logs
- pass the secret as a command-line argument
- silently select another provider if Agnes authentication fails

Deleting the isolated profile deletes FirstWindow's stored copy of that key.

## Project-directory safety

Older Hermes one-shot releases had a working-directory bug where file tools could operate in a stale or home directory even when the process was launched from a project folder.

FirstWindow therefore applies several independent pins:

- subprocess cwd = selected project
- `hermes --in <project>`
- `--no-restore-cwd`
- `TERMINAL_CWD=<project>`

A current Hermes release should honor `--in`; the extra environment pin keeps older compatible releases fail-safe.

## Durable Resume

Every task gets repository-local durable state under `.firstwindow/tasks/<task_id>/`.

FirstWindow records the objective, acceptance criteria, checkpoint, next action, evidence, and execution attestation. Resume continues the same task ID from that state instead of relying on hidden chat history.
CLI equivalent:

```bash
firstwindow tasks --project .
firstwindow resume <task_id> --project .
```

## Verification: execution is not completion

For the default beginner task, FirstWindow creates two acceptance criteria:

1. **AC-001** — agent execution completed through the verified route.
2. **AC-002** — the requested task outcome was independently verified.

The executor can automatically cover AC-001. It cannot automatically cover AC-002 merely by saying “done”.

Until independent evidence is recorded:

```text
COVERED AC-001
UNCOVERED AC-002
NOT VERIFIED
```

After an actual check is recorded for AC-002, `firstwindow verify` can become VERIFIED.

For custom workflows, supply explicit acceptance criteria:

```bash
firstwindow run "Add a /health endpoint" \
  --accept "tests pass" \
  --accept "GET /health returns 200"
```

Then attach real evidence to the corresponding criterion IDs before verification.
## Demo Project

Press **Create Demo** or run:

```bash
firstwindow demo
```

## What FirstWindow automates

- Hermes runtime detection/install flow
- isolated Hermes → Agnes API provider configuration
- strict no-fallback $0 routing
- live readiness probe
- Hermes usage attestation
- project-directory pinning
- task/checkpoint/evidence state
- durable resume
- verification coverage reporting

## What remains intentionally interactive

- approving runtime installation
- entering your Agnes API key
- confirming that your Agnes account/key route is free
- choosing/downloading a Hermes local model when using local fallback
- providing or approving independent evidence for task-specific acceptance

These interactions are deliberate security/cost boundaries, not missing automation.

## Windows SmartScreen and signing

The community binary may be unsigned. Windows SmartScreen can therefore show an unknown-publisher warning.

FirstWindow does not claim otherwise. The Release includes `SHA256SUMS.txt`, generated from the packaged EXE so you can verify the download.
