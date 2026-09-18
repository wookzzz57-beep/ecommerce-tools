# FirstWindow Post-Release Launch Control

This document governs FirstWindow after a verified release exists and the product baseline must remain stable while distribution and real-user evidence are collected.

## Purpose

Post-release work is not normal engineering work.

The goal is to learn where the real adoption funnel breaks without reopening product scope by default:

```text
Exposure
  ↓
Repository / site visit
  ↓
Understand the promise
  ↓
Trust the download
  ↓
Download / open
  ↓
Reach a usable $0 path
  ↓
Complete a first task
  ↓
Return / recommend / star
```

A star is a discovery/trust signal. It is not proof that the product works, is retained, or deserves a feature change.

## Canonical post-release state

Use:

- `status = "post-release"`
- `active_engineering_issue = null`
- `engineering_queue = []`
- non-empty `launch_track`
- `launch_control.active_issue == launch_track[0]`
- `launch_control.experiment_wip_limit = 1`
- `launch_control.product_baseline_frozen = true`

The first issue in `launch_track` is the only active launch work item. Later items are queued.

The released version remains the product baseline until a separately scoped engineering issue is promoted and accepted.

## Launch experiment packet

Every material distribution experiment should define:

1. **Objective** — what funnel uncertainty is being reduced.
2. **Audience/channel** — where and for whom.
3. **Hypothesis** — what is expected to change and why.
4. **Artifact** — post, demo, README/site change, or other bounded asset.
5. **Primary signal** — the smallest observable outcome that can test the hypothesis.
6. **Evidence source** — public page, release signal, analytics, or direct user report.
7. **Window** — when the experiment is evaluated.
8. **Success rule** — what justifies keeping or repeating it.
9. **Stop rule** — what ends it early.
10. **Decision** — continue, revise, discard, or promote a product problem.

Do not run multiple materially different launch experiments at the same time if their effects cannot be distinguished.

## Evidence hierarchy

Prefer evidence in this order:

1. reproducible product or download failure;
2. direct first-user observation tied to an exact step;
3. repeated independent reports of the same friction;
4. observable conversion signal such as release/download activity;
5. repository visits/stars;
6. opinions or isolated preferences.

Lower levels can guide the next experiment but should not override stronger contradictory evidence.

## Feedback triage

### Immediate engineering candidate

Open a scoped issue immediately for:

- security regression,
- hidden/unknown-cost behavior,
- broken download or startup,
- release integrity/checksum failure,
- data/credential exposure,
- a reproducible P0/P1 beginner-path failure.

Pause launch experiments until the issue is triaged.

### Evidence-backed product candidate

Repeated onboarding friction may be promoted when:

- the same problem appears in multiple independent observations, or
- one observation is reproducible and blocks the core beginner flow,
- the proposed change has a bounded scope,
- acceptance can be verified deterministically.

### Backlog only

Feature requests, preferences, and speculative improvements stay outside active engineering until problem evidence exists.

## Promotion gate: feedback → engineering

Launch evidence cannot silently mutate product scope.

To promote a problem into engineering:

1. create a new GitHub issue;
2. state the user problem and evidence;
3. freeze objective, scope, non-goals, risks, acceptance, and stop conditions;
4. transition `PROJECT_STATE.json` from `post-release` to an engineering-active state;
5. put exactly one issue first in `engineering_queue`;
6. create an isolated branch;
7. keep the launch track recorded but paused unless the engineering issue is launch-safe;
8. verify and merge before resuming normal launch work.

## Long-task and context-loss contract

Before handoff or a long pause, record in the active launch issue and/or `PROJECT_STATE.json.resume_point`:

- active experiment,
- exact artifact/channel,
- completed actions,
- evidence already collected,
- baseline and current signal if known,
- blockers,
- unresolved uncertainty,
- exact next action,
- whether product engineering remains frozen.

Never reconstruct launch state from memory when canonical evidence is available.

## Anti-degradation rules

Stop and reload canonical state when:

- stars become the goal instead of evidence about adoption;
- a channel-specific tactic starts changing the product without promotion;
- more than one launch experiment is active and attribution becomes ambiguous;
- a feature is being built because of one unverified comment;
- a paid/spam/deceptive acquisition tactic is proposed;
- a claim is stronger than the evidence supporting it;
- the release baseline changes without an engineering issue and verification.

## Integrity boundaries

FirstWindow launch work must not use:

- fake stars, purchased engagement, engagement exchanges, or sockpuppets;
- spam posting or unsolicited bulk outreach;
- fabricated users, testimonials, screenshots, downloads, or metrics;
- deceptive "$0" claims;
- hidden tracking as a condition of use.

## Acceptance of a launch cycle

A launch cycle closes only when it produces one of these:

- the target adoption milestone with real evidence;
- a clearly identified dominant funnel blocker;
- a reproducible product problem promoted into a scoped issue;
- evidence that the tested hypothesis should be discarded.

"Posted content" alone is not acceptance.
